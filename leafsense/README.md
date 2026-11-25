# Leaf Sense – setup in VS Code

1. Install: Python 3.10+, MySQL Server + Workbench, VS Code (with the *Python* extension).
2. Open this folder in VS Code (File > Open Folder).
3. Terminal > New Terminal, then:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt python-dotenv
   ```
   VS Code: Ctrl+Shift+P > "Python: Select Interpreter" > choose `venv`.
4. In MySQL Workbench open `schema.sql` and run it (lightning icon).
5. Copy `.env.example` to `.env` and put your MySQL password in it.
6. Run: `streamlit run app.py`  (opens http://localhost:8501)
7. Register, add plants (tick "control" for always-watered ones), upload one photo per day.
