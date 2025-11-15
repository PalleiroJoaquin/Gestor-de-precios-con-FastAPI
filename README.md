 🏷️ Gestor de Precios — API REST con FastAPI

Una API REST simple, moderna y profesional para gestionar productos, precios y aumentos masivos.  
Hecha con **FastAPI + SQLModel + SQLite**, ideal como backend base para cualquier sistema comercial.

No es contabilidad, no es un ERP gigante.  
Es una API clara, rápida y útil para automatizar tareas comunes en negocios que manejan productos.

---

## 🚀 Características principales

- ➕ **Crear productos** (nombre, categoría, costo y precio)
- 📄 **Listar / buscar productos**
- ✏️ **Actualizar productos** con historial automático si cambia el precio
- ❌ **Eliminar productos**
- 📈 **Aumentar precios masivamente** por categoría o a todo el catálogo
- 🕒 **Historial completo de cambios** (precio anterior, nuevo, motivo)
- 🗂️ **Documentación automática Swagger** con `/docs`

---

## 🧠 Tecnologías utilizadas

- **FastAPI** — Framework moderno para APIs
- **SQLModel** — ORM basado en SQLAlchemy + Pydantic
- **SQLite** — Base de datos liviana y portable
- **Uvicorn** — Servidor ASGI rápido

---

## 📦 Instalación

Cloná el repositorio:

```bash
git clone https://github.com/PalleiroJoaquin/Gestor-de-precios-con-FastAPI.git
cd Gestor-de-precios-con-FastAPI
cd tu-repo
Instalá las dependencias con:
pip install -r requirements.txt

Ejecutala con:
uvicorn main:app --reload
Entrá al browser de tu elección y poné:
http://127.0.0.1:8000/docs
