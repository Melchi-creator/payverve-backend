# Payverve Backend

## About Payverve

Payverve is a fintech application designed to facilitate financial transactions for Nigerians, providing them with the
capability to manage dollar and pound accounts, swap currencies, create virtual cards, and more. The backend of this
application is built using FLASK, a high-level Python web framework known for its robustness and scalability.

## Features

- Multi-Currency Support: Users can create and manage dollar and pound accounts within the application.
- Currency Swapping: Exchange currencies seamlessly within the app to meet various financial needs.
- Virtual Card Creation: Generate virtual cards for online transactions, providing added security and convenience.
- Scalable Architecture: Built on FLASK, ensuring a stable and scalable backend for handling a large number of users
  and transactions.

## Requirements

- Python 3.x
- Flask
- Additional dependencies as specified in requirements.txt

## Setup

**Virtual Environment**

Create a virtual environment to manage project dependencies and isolate them from other projects.

### Development Environment

#### Virtual environment

##### for PyCharm

- Open your project in PyCharm.
- Navigate to File > Settings > Project: <project_name> > Python Interpreter.
- Click on the gear icon and select Add....
- Choose Virtualenv Environment and specify the location.
- Select the base interpreter (Python 3.x) and click OK.

##### for VSCode

- Open your project in VSCode.
- Open the integrated terminal (Ctrl+` ).
- Run the following command to create a virtual environment:

    ```Copy code
    python -m venv venv
    ```
- Activate the virtual environment:

  **On Windows:**
    ```Copy code
    source venv/Scripts/activate
    ````
  **On macOS/Linux:**
    ```Copy code
    source venv/bin/activate
    ```

#### Installing Dependencies

Install the required dependencies using `pip`.

- for development

    ```Copy code
    pip install -r requirements.txt
    ```

- for production

    ```Copy code
    pip install -r prod-requirements.txt
    ```

#### Database setup

- Configure your database settings in `.env` and perform migrations to initialize the database schema.
- To perform migrations run:

    ```Copy code
    flask db upgrade
    ```

#### Run server application

- Run the Flask development server to start the backend application.

    ```Copy code
    export flask_app=src/server.py
    ```

    ```Copy code
    export flask_debug=true
    ```

    ```Copy code
    python -m src.server
    ```

Access the application at http://127.0.0.1:3100/payverve/ in your web browser.

Now, the backend of Payverve is set up and ready to handle financial transactions and operations efficiently.

