from flask import Flask, request, render_template

# Create a new Flask application instance
app = Flask(__name__)

# Define a route for the root URL ('/') that accepts both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def index():
    # Check if the request method is POST
    if request.method == 'POST':
        try:
            # Get the values of 'num1' and 'num2' from the form data, defaulting to 0 if not provided
            num1 = float(request.form.get('num1', 0))
            num2 = float(request.form.get('num2', 0))
            # Calculate the sum of num1 and num2
            result = num1 + num2
            # Render the 'index.html' template with the result
            return render_template('index.html', result=result)
        except ValueError:
            # If a ValueError occurs (e.g., invalid input), render the 'index.html' template with an error message
            return render_template('index.html', error="Invalid input. Please enter numeric values.")
    # If the request method is GET, render the 'index.html' template without any result or error
    return render_template('index.html')

# Check if the script is being run directly (not imported as a module)
if __name__ == '__main__':
    import os

    # Get the value of the 'FLASK_DEBUG' environment variable and convert it to a boolean
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    # Run the Flask application with the specified debug mode
    app.run(debug=debug_mode)

