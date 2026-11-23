# 🥕 VSE ALIMENTA

**Prototipo web adaptable a celulares para conectar donantes de alimentos con comedores populares de Villa El Salvador.**

Proyecto académico para **HackODS UA 2026**. Vinculado principalmente con el **ODS 2: Hambre Cero** y complementariamente con el **ODS 12: Producción y Consumo Responsables**.

> Los registros precargados son ficticios y sirven únicamente para demostrar el funcionamiento. El prototipo no representa una red real de donantes ni de comedores verificados.

## 1. Problema y propuesta

VSE ALIMENTA busca facilitar la coordinación entre personas, mercados o comercios que tienen alimentos aptos para donar y comedores populares que han registrado una necesidad.

La aplicación permite:

1. Publicar una donación indicando alimento, categoría, cantidad, zona y fecha/hora límite de recojo.
2. Registrar la necesidad de un comedor popular.
3. Encontrar coincidencias y explicar por qué se recomienda cada una.
4. Reservar una cantidad concreta de una donación para una necesidad.
5. Confirmar la entrega o cancelar una reserva pendiente.
6. Consultar indicadores de kilos disponibles, kilos entregados, reservas pendientes y comedores atendidos.

## 2. Arquitectura

```text
Navegador (PC / celular)
          |
          v
  app.py - Interfaz Streamlit
          |
          +----------------------+
          |                      |
          v                      v
 database.py               matching.py
 Persistencia SQLite       Reglas de compatibilidad
          |                      |
          +----------+-----------+
                     |
                     v
             vse_alimenta.db
```

### Componentes

| Archivo | Responsabilidad |
|---|---|
| `app.py` | Interfaz web, formularios, navegación, panel, reservas y entregas. |
| `database.py` | Esquema SQLite, datos demo, altas, consultas, reservas y confirmaciones. |
| `matching.py` | Puntaje de coincidencia y explicación de recomendaciones. |
| `requirements.txt` | Dependencias de Python. |
| `tests/test_matching.py` | Pruebas básicas de las reglas de emparejamiento. |

### Tecnologías

- **Python 3.10 o superior**: lenguaje principal.
- **Streamlit**: interfaz web adaptable a diferentes tamaños de pantalla.
- **SQLite**: base de datos local, sin servidor adicional.
- **Git y GitHub**: control de versiones y entrega del repositorio.

## 3. Instalación y ejecución local

### Requisitos

- Python 3.10 o superior.
- Conexión a internet para instalar Streamlit la primera vez.

### Windows (PowerShell o CMD)

1. Descarga o clona este repositorio.
2. Abre una terminal dentro de la carpeta `vse-alimenta-hackods-2026`.
3. Crea un entorno virtual (recomendado):

```bash
python -m venv .venv
```

4. Actívalo:

```bash
.venv\Scripts\activate
```

5. Instala las dependencias:

```bash
python -m pip install -r requirements.txt
```

6. Ejecuta la aplicación:

```bash
python -m streamlit run app.py
```

7. Streamlit abrirá la aplicación en el navegador, normalmente en `http://localhost:8501`.

También se puede ejecutar `run_windows.bat` en Windows para instalar y abrir la aplicación automáticamente.

### Probar desde un celular conectado al mismo Wi-Fi

1. Conecta la computadora y el celular a la misma red Wi-Fi.
2. En la computadora ejecuta:

```bash
python -m streamlit run app.py --server.address 0.0.0.0
```

3. En Windows ejecuta `ipconfig` y localiza la dirección IPv4 de la tarjeta Wi-Fi (por ejemplo, `192.168.1.20`).
4. En el navegador del celular abre `http://DIRECCION-IP-DE-LA-PC:8501` (por ejemplo, `http://192.168.1.20:8501`).
5. Si Windows Firewall pregunta, permite el acceso en la red privada durante la demostración.

Esta forma de acceso es para una demo en una red local confiable. No publiques el prototipo abierto a internet ni uses datos personales reales: esta versión todavía no incorpora autenticación ni controles de acceso.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 4. Cómo probar la demo en vivo

La primera vez que se inicia la aplicación, SQLite crea automáticamente la base de datos y carga ejemplos ficticios.

Guion sugerido para una demostración de 90 segundos:

1. **Panel principal:** mostrar kilos disponibles y los indicadores.
2. **Registrar donación:** publicar, por ejemplo, 8 kg de arroz con un plazo de recojo futuro.
3. **Registrar necesidad:** crear una necesidad de 5 kg de arroz para un comedor.
4. **Emparejar y reservar:** observar la coincidencia sugerida, leer sus razones y reservar 5 kg.
5. **Entregas:** confirmar la recepción.
6. **Panel principal:** mostrar cómo cambian los kilos disponibles y entregados.

Para repetir la demostración, abre **Herramientas de demostración** en el menú lateral, marca la confirmación y pulsa **Restablecer datos demo**. Esta acción borra todos los registros guardados y vuelve a cargar los ejemplos ficticios.

## 5. Cómo funciona el emparejamiento

El prototipo utiliza reglas transparentes; **no afirma utilizar inteligencia artificial ni un modelo predictivo entrenado**.

| Criterio | Puntaje |
|---|---:|
| Coincidencia exacta del nombre del alimento | 50 |
| Coincidencia por categoría, si el nombre no es exacto | 28 |
| Misma zona | 20 |
| Zona diferente | 7 |
| Donación vence en 6 horas o menos | 20 |
| Donación vence en 24 horas o menos | 12 |
| Donación con plazo más amplio | 5 |
| Cantidad disponible cubre toda la necesidad pendiente | 10 |
| La cantidad disponible cubre una parte | 6 |

Solo se comparan alimentos con el mismo nombre o la misma categoría. Se excluyen donaciones y necesidades vencidas o sin cantidad pendiente. El resultado incluye el puntaje y las razones de la recomendación.

## 6. Reglas de reserva y entrega

- No se puede reservar una cantidad mayor que la disponible en la donación.
- No se puede reservar más de lo que el comedor aún necesita.
- La reserva se guarda en una transacción SQLite para reducir el riesgo de sobreasignación.
- Una reserva pendiente descuenta temporalmente la cantidad disponible.
- Una entrega confirmada sigue descontando la cantidad, porque el alimento ya fue asignado y entregado.
- Una reserva cancelada libera nuevamente la cantidad.

## 7. Pruebas básicas

Desde la carpeta raíz del proyecto:

```bash
python -m unittest discover -s tests -v
```

## 8. Organización sugerida para dos integrantes

| Integrante | Responsabilidades |
|---|---|
| Integrante 1 | Interfaz en `app.py`, formularios, diseño adaptable y demo de navegación. |
| Integrante 2 | `database.py`, `matching.py`, pruebas, validación de reservas y documentación GitHub. |

Ambos deben revisar juntos el flujo completo antes de congelar el código.

## 9. Publicación en GitHub

Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Primera versión funcional de VSE ALIMENTA"
git branch -M main
git remote add origin https://github.com/USUARIO/vse-alimenta-hackods-2026.git
git push -u origin main
```

Sustituye `USUARIO` por el nombre real de la cuenta u organización de GitHub. No subas la base de datos local (`vse_alimenta.db`) ni información personal real.

## 10. Limitaciones y siguientes pasos

Esta versión es una **demo funcional de alcance académico**. Antes de usarla en una operación real se necesitaría, como mínimo:

- Autenticación y permisos para donantes, comedores y administradores.
- Verificación de identidad y de las organizaciones participantes.
- Protección de teléfonos, direcciones y otros datos personales.
- Validaciones sanitarias, trazabilidad, condiciones de almacenamiento y cadena de frío.
- Coordinación real de transporte, recojo, horarios y responsables.
- Base de datos administrada y copias de seguridad si se despliega en internet.

La aplicación no certifica que un alimento sea seguro. La persona u organización responsable debe revisar su estado, procedencia, fechas y condiciones de conservación antes de aceptarlo o distribuirlo.

---

**VSE ALIMENTA — La tecnología conecta. La comunidad transforma.**
