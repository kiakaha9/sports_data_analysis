import os
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
from peewee import *

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SqliteDatabase('sports_data.db')

class BaseModel(Model):
    class Meta:
        database = db

class Game(BaseModel):
    team = CharField()
    opponent = CharField()
    points = IntegerField()
    date = DateField()

with db:
    db.create_tables([Game])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    teams = Game.select(Game.team).distinct()
    return render_template('index.html', teams=teams)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            return render_template('upload.html', error="Nav izvēlēts fails")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            df = pd.read_csv(filepath)

            for _, row in df.iterrows():
                Game.create(
                    team=row['team'],
                    opponent=row['opponent'],
                    points=row['points'],
                    date=pd.to_datetime(row['date']).date()
                )
            return redirect(url_for('results'))
    return render_template('upload.html')

@app.route('/results')
def results():
    selected_team = request.args.get('team')
    if selected_team:
        games = Game.select().where(Game.team == selected_team)
    else:
        games = Game.select()

    df = pd.DataFrame(list(games.dicts()))

    plt.figure(figsize=(8, 4))
    avg_points = df.groupby('team')['points'].mean()
    avg_points.plot(kind='bar', color='skyblue')
    plt.title('Vidējie punkti pēc komandas')
    plt.ylabel('Punkti')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(UPLOAD_FOLDER, 'bar_chart.png'))
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.hist(df['points'], bins=10, color='green', edgecolor='black')
    plt.title('Punktu sadalījuma histogramma')
    plt.xlabel('Punkti')
    plt.ylabel('Spēļu skaits')
    plt.tight_layout()
    plt.savefig(os.path.join(UPLOAD_FOLDER, 'histogram.png'))
    plt.close()

    plt.figure(figsize=(8, 4))
    df_sorted = df.sort_values(by='date')
    plt.plot(df_sorted['date'], df_sorted['points'], marker='o', linestyle='-')
    plt.title('Punkti laika gaitā')
    plt.ylabel('Punkti')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(UPLOAD_FOLDER, 'line_chart.png'))
    plt.close()

    teams = Game.select(Game.team).distinct()
    return render_template('results.html', team=selected_team, teams=teams)

if __name__ == '__main__':
    app.run(debug=True)
