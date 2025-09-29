## Generador de Horóscopos con Trigramas

Este no es un oráculo místico. Es un generador de horóscopos retro-NLP, donde la magia no viene de los astros, sino de un viejo conocido: los modelos de lenguaje basados en trigramas.

Un trigrama es basicamente un modelo que predice la próxima palabra en base a las dos anteriores. Nada de “conexión cósmica con el universo”, pura probabilidad condicional. 

Así se hacía NLP antes de los Transformers, cuando los modelos cabían en un disquete y no necesitabas dejar de comer para comprar una GPU.

Claro, a veces los resultados suenan más como Yoda con insomnio que como un horóscopo real. Pero con algunos trucos clásicos —como 4-gram con backoff o un Kneser-Ney modificado para trigram/4-gram— los resultados pueden ser bastante buenos.

Lo mejor: estos modelos pesan lo mismo que un sticker de WhatsApp. Menos de 5 MB en JSON y bajo 1 MB comprimidos. Por eso podemos portarlos modelos directamente al navegador nada de APIs o pagar por token.

No es magia, es estadística.

### ¿Qué hace y qué NO hace?
- *Hace:* aprende patrones locales de palabras del corpus (e.g., “hoy”, “en el amor”, “trabajo”, “número de suerte”) y genera nuevos textos similares combinando esas piezas con probabilidades.
- *NO hace:* no “adivina” el futuro. Solo modela lenguaje: estima qué palabra suele seguir a otras dos (trigrama).

## ¿Cómo funciona?

La probabilidad de una secuencia de palabras \( w_1, \dots, w_T \) se puede descomponer paso a paso como un producto de probabilidades condicionales:

$$
P(w_1,\dots,w_T) = \prod_{t=1}^{T} P\!\left(w_t \mid w_1,\dots,w_{t-1}\right).
$$

> En otras palabras: para calcular la probabilidad de toda la frase, vamos multiplicando la probabilidad de cada palabra sabiendo lo que vino antes.

### El problema: todo el pasado es demasiado

Si intentáramos condicionar en **todas** las palabras anteriores, el cálculo sería intratable (_demasiado complejo, porque habría infinitas combinaciones posibles_).

Por eso hacemos una aproximación de Markov:
- Bigramas (orden 1): Cada palabra depende solo de la palabra anterior.
- Trigramas (orden 2): Cada palabra depende de las dos palabras anteriores.

Para Trigramas entonces, la fórmula se simplifica a:

$$
P\!\left(w_t \mid w_1,\dots,w_{t-1}\right) \approx P\!\left(w_t \mid w_{t-2}, w_{t-1}\right).
$$

### ¿Cómo entrenamos el modelo?

1.	Recorremos el corpus (todos los horóscopos).
2.	Contamos cuántas veces aparece cada tripleta $(w_{t-2}, w_{t-1}, w_t)$.
3.	Estimamos las probabilidades con máxima verosimilitud (MLE):


$$
\hat{P}(w \mid u,v) = \frac{\text{count}(u,v,w)}{\sum_{w'} \text{count}(u,v,w')}\,.
$$

> Es decir: de todas las veces que vimos (u,v), ¿con qué frecuencia vino después w?

Para evitar ceros se puede usar un **suavizado** sencillo (e.g. add-1/Laplace):

$$
\hat{P}_{\text{add-1}}(w \mid u,v) = \frac{\text{count}(u,v,w) + 1}{\sum_{w'} \big(\text{count}(u,v,w') + 1\big)} = \frac{\text{count}(u,v,w) + 1}{\text{count}(u,v,*) + V}\,,
$$

Donde:
- $\text{count}(u,v,*)$ = número total de veces que vimos el par (u,v).
- $V$ = tamaño del vocabulario.

### Generación de texto

Una vez entrenado, el modelo puede generar frases nuevas:
1.	Partimos de un estado inicial.
2.	Muestreamos la siguiente palabra según la distribución aprendida \hat{P}(\cdot \mid u,v).
3.	Avanzamos la ventana y repetimos hasta llegar a un token de fin o a una longitud máxima.

> Así, aunque el modelo no entiende el lenguaje, produce frases nuevas que “suenan” parecidas al corpus porque respeta las probabilidades observadas.