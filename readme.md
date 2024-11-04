exam/
│
├── app/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   ├── __init__.py        # Contains create_app() function
│   ├── routes.py          # Contains route definitions
│   └── models.py          # Database models
│    
├── instance/
│   └── app.db             # SQLite database file
├── config.py              # Configuration settings
├── application.py         # Entry point, renamed from run.py
└── requirements.txt       # Dependencies list