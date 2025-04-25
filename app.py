import os
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', error="No file selected.")
        
        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', error="No file selected.")
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return redirect(url_for('results', filename=filename))
    return render_template('upload.html')

@app.route('/results/<filename>')
def results(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        df = pd.read_csv(filepath)

        if 'Team' not in df.columns or 'Points' not in df.columns:
            return "CSV must contain 'Team' and 'Points' columns."

        plt.figure(figsize=(10,6))
        df.groupby('Team')['Points'].mean().plot(kind='bar')
        plt.title('Average Points by Team')
        plt.ylabel('Points')
        plt.xticks(rotation=45)
        plt.tight_layout()

        plot_path = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
        plt.savefig(plot_path)
        plt.close()

        return render_template('results.html', filename='plot.png')
    
    except Exception as e:
        return f"Error processing file: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)