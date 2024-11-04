from app import create_app

application = create_app()  # This should be `application`, not `app`

if __name__ == '__main__':
    application.run(host='127.0.0.1', port=5000)
