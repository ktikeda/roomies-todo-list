from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from roomies_todo_list import app, db, forms
from .models import User, UserSchema, Task, TaskSchema, TaskAssignee
from http import HTTPStatus
from datetime import datetime
from werkzeug import urls

# Error Handling Imports
from .errors import BadRequest
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError

API = "/api"


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return ""


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urls.url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


# USER ROUTES
@app.route(API + "/users", methods=["POST"])
def add_user():
    try:
        data = UserSchema().load(request.get_json().get("user"))
        new_user = User(**data)
    except ValidationError as e:
        raise BadRequest(e.messages)

    try:
        db.session.add(new_user)
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise BadRequest("Email or username is already taken.")
    else:
        db.session.commit()
        body = {"user": UserSchema().dump(new_user)}
        return jsonify(body), HTTPStatus.CREATED


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User( #TODO validate
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, you are now a registered user!")
        except ValidationError as e:
            raise BadRequest(e.messages)

        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route(API + "/users", methods=["GET"])
def get_all_users():
    all_users = User.query.all()
    body = {"users": UserSchema().dump(all_users, many=True)}

    return jsonify(body), HTTPStatus.OK


@app.route(API + "/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)

    if not user:
        raise BadRequest("Resource not found.", status=HTTPStatus.NOT_FOUND)

    body = {"user": UserSchema().dump(user)}

    return jsonify(body), HTTPStatus.OK


@app.route(API + "/users/<int:user_id>", methods=["PATCH"])
def update_user(user_id):
    user = User.query.get(user_id)

    if not user:
        raise BadRequest("Resource not found.", status=HTTPStatus.NOT_FOUND)
    try:
        data = UserSchema(partial=True).load(request.get_json().get("user"))
    except ValidationError as e:
        raise BadRequest(e.messages)

    for attr, val in data.items():
        setattr(user, attr, val)

    user.updated_at = datetime.now()
    db.session.add(user)
    db.session.commit()

    body = {"user": UserSchema().dump(user)}

    return jsonify(body), HTTPStatus.OK


@app.route(API + "/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        User.query.filter(User.id == user.id).delete()
        db.session.commit()
    else:
        raise BadRequest("Resource not found.", status=HTTPStatus.NOT_FOUND)

    return "", HTTPStatus.NO_CONTENT


# TASK ROUTES
@app.route(API + "/tasks", methods=["POST"])
def add_task():
    # Check against TaskSchema
    try:
        data = TaskSchema(partial=("created_by.username", "created_by.email")).load(
            request.get_json().get("task")
        )
    except ValidationError as e:
        raise BadRequest(e.messages)

    # Check that user exists
    user_id = int(data["created_by"]["id"])
    del data["created_by"]
    user = User.query.get(user_id)
    if user:
        new_task = Task(created_by=user, **data)
    else:
        raise BadRequest("User not found.", status=HTTPStatus.NOT_FOUND)

    # Add task to database
    try:
        db.session.add(new_task)
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise BadRequest("Something went wrong.")
    else:
        db.session.commit()
        body = {"task": TaskSchema().dump(new_task)}
        return jsonify(body), HTTPStatus.CREATED


@app.route(API + "/tasks", methods=["GET"])
def get_all_tasks():
    all_tasks = Task.query.all()
    body = {"tasks": TaskSchema().dump(all_tasks, many=True)}

    return jsonify(body), HTTPStatus.OK


@app.route(API + "/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        raise BadRequest("Resource not found.", status=HTTPStatus.NOT_FOUND)

    body = {"task": TaskSchema().dump(task)}

    return jsonify(body), HTTPStatus.OK


@app.route(API + "/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        raise BadRequest("Resource not found.", status=HTTPStatus.NOT_FOUND)
    try:
        data = TaskSchema(partial=True).load(request.get_json().get("task"))
    except ValidationError as e:
        raise BadRequest(e.messages)

    existing_assignees = set(task.assignees)
    print(existing_assignees)
    new_assignees = set()
    for assignee in data.get("assignees", []):
        user = User.query.get(assignee["id"])
        if user:
            new_assignees.add(user)
        else:
            raise BadRequest("User not found.", status=HTTPStatus.NOT_FOUND)

    to_remove = existing_assignees - new_assignees
    to_add = new_assignees - existing_assignees
    print(f"to_remove: {to_remove}")
    print(f"to_add: {to_add}")
    try:
        for user in to_add:
            new_assignee = TaskAssignee(task_id=task.id, user_id=user.id)
            db.session.add(new_assignee)

        for user in to_remove:
            old_assignee = TaskAssignee.query.filter(
                TaskAssignee.user_id == user.id, TaskAssignee.task_id == task.id
            ).first()
            if old_assignee:
                db.session.delete(old_assignee)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise BadRequest(f"Something went wrong: {e}")

    data.pop("assignees", None)

    for attr, val in data.items():
        setattr(task, attr, val)

    task.updated_at = datetime.now()
    db.session.add(task)
    db.session.commit()

    body = {"task": TaskSchema().dump(task)}

    return jsonify(body), HTTPStatus.OK


@app.route(API + "/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        Task.query.filter(Task.id == task.id).delete()
        db.session.commit()
    else:
        raise BadRequest("Resource not found.", status=HTTPStatus.NOT_FOUND)

    return "", HTTPStatus.NO_CONTENT

