from main import db, Users

db.session.delete(Users.query.get(2))
db.session.commit()

