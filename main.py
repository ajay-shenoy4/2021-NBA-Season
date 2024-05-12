# project: p4
# submitter: ashenoy3
# partner: none
# hours: 35

import pandas as pd
from flask import Flask, request, jsonify, render_template
import re
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
df = pd.read_csv("main.csv")

# A/B Testing Variables
homepage_counter = 0
current_version = "A"
best_version = None
version_A_clicks = 0
version_B_clicks = 0

# Rate Limiting Variables
ip_visits = {}

# Browse Page
@app.route('/')
def home():
    global homepage_counter, current_version, best_version, version_A_clicks, version_B_clicks

    # A/B Testing Logic
    homepage_counter += 1
    if homepage_counter <= 10:
        current_version = "A" if homepage_counter % 2 != 0 else "B"
    elif homepage_counter == 11:
        best_version = current_version

    # Load the corresponding version of the homepage
    if best_version:
        version_to_load = best_version
    else:
        version_to_load = current_version

    return render_template(f"index_{version_to_load}.html")

@app.route('/browse.html')
def browse():
    return render_template('browse.html', columns=df.columns, rows=df.values)


@app.route('/browse.json')
def browse_json():
    if request.remote_addr in ip_visits:
        return jsonify(ip_visits[request.remote_addr])
    return jsonify([])

@app.route('/donate.html')
def donate():
    return render_template('donate.html')

num_subscribed = 0

@app.route('/email', methods=["POST"])
def email():
    global num_subscribed
    email = str(request.data, "utf-8")
    if re.match(r"^[^@]+@[^@]+\.[a-zA-Z]{3}$", email) and "@" in email:
        with open("emails.txt", "a") as f:
            f.write(email + "\n")
        num_subscribed += 1
        return jsonify(f"Thanks, your subscriber number is {num_subscribed}!")
    return jsonify("Stop being so careless with your email!")

# Rate Limiting Logic
@app.before_request
def before_request():
    if request.path == '/browse.json':
        if request.remote_addr in ip_visits:
            ip_visits[request.remote_addr] += 1
        else:
            ip_visits[request.remote_addr] = 1
        if ip_visits[request.remote_addr] > 1:
            return jsonify("Rate limit exceeded. Please wait before making another request."), 429

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False)

# First SVG: Points per Game per Age
fig, ax = plt.subplots()
df.boxplot(column="PTS", by="Age", ax=ax)
ax.set_xlabel("Age")
ax.set_ylabel("Points per Game")
ax.set_title("Points per Game per Age")
plt.tight_layout()
plt.savefig("static/dashboard_1.svg")
plt.close(fig)

# Second SVG: FG% per Position
fig, ax = plt.subplots()
df.boxplot(column="FG%", by="Pos", ax=ax)
ax.set_xlabel("Position")
ax.set_ylabel("FG%")
ax.set_title("Field Goal Percentage per Position")
plt.tight_layout()
plt.savefig("static/dashboard_2.svg")
plt.close(fig)

# Third SVG: 3P% per Age
fig, ax = plt.subplots()
df.boxplot(column="3P%", by="Age", ax=ax)
ax.set_xlabel("Age")
ax.set_ylabel("3P%")
ax.set_title("Three Point Percentage per Age")
plt.tight_layout()
plt.savefig("static/dashboard_3.svg")
plt.close(fig)

# Fourth SVG: Player Scatter eFG% vs PTS
fig, ax = plt.subplots()
df.plot.scatter(x="eFG%", y="PTS", ax=ax)
ax.set_xlabel("eFG%")
ax.set_ylabel("PTS")
ax.set_title("Scatter Plot: eFG% vs PTS")
plt.tight_layout()
plt.savefig("static/dashboard_4.svg")
plt.close(fig)

# Fifth SVG: Fill Between Graph - Assists vs Turnovers
x = df['AST']
y = df['TOV']
coefficients = np.polyfit(x, y, 1)
line_of_best_fit = np.poly1d(coefficients)
upper_boundary = line_of_best_fit(x) + 1
lower_boundary = line_of_best_fit(x) - 1
fig, ax = plt.subplots()
ax.scatter(x, y, c='blue', alpha=0.5, label='Data')
ax.plot(x, line_of_best_fit(x), color='red', label='Line of Best Fit')
ax.plot(x, upper_boundary, color='green', linestyle='--', label='Upper Boundary')
ax.plot(x, lower_boundary, color='purple', linestyle='--', label='Lower Boundary')
ax.set_xlabel('Assists')
ax.set_ylabel('Turnovers')
ax.set_title('Scatter Plot with Line of Best Fit and Boundaries: Assists vs Turnovers')
ax.legend()
plt.tight_layout()
plt.savefig("static/dashboard_5.svg")
plt.close(fig)

# Sixth SVG: Scatter Plot with Line of Best Fit and Highlighted Points of MPG vs Total Counting Stats
df["Total"] = df['TRB'] + df['AST'] + df['STL'] + df['BLK'] + df['PTS'] - df['TOV']
fig, ax = plt.subplots()
ax.scatter(df['MP'], df['Total'], c='blue', alpha=0.5, label='All Points')
fit = np.polyfit(df["MP"], df["Total"], 1)
ax.plot(df["MP"], fit[0] * df["MP"] + fit[1], color="red", label='Line of Best Fit')
highlighted_points = df[(df['Total'] - (fit[0] * df['MP'] + fit[1])).abs() >= 8]
ax.scatter(highlighted_points['MP'], highlighted_points['Total'], c='yellow', marker='o', s=100, label='Highlighted Points')
ax.set_xlabel('MPG')
ax.set_ylabel('Sum of TRB, AST, STL, BLK, PTS, - Turnovers')
ax.set_title('Scatter Plot: MPG vs Sum of TRB, AST, STL, BLK, PTS, - Turnovers')
ax.legend()
highlighted_points = df[(df["Total"] - (fit[0] * df["MP"] + fit[1])).abs() >= 8]
ax.scatter(highlighted_points["MP"], highlighted_points["Total"], color="yellow", marker="o", s=100)
plt.tight_layout()
plt.savefig("static/dashboard_6.svg")
plt.close(fig)

# NOTE: app.run never returns (it runs forever unless you kill the process)
# Thus, don't define any functions after the app.run call because it will
# never get that far.