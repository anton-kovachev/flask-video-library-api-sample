from flask import Flask, abort
from flask_restful import Api, Resource, reqparse, marshal_with, fields, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class VideoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    views = db.Column(db.Integer, nullable=False, default=0)
    
    def __repr__(self):
        return str({ 'title': self.title, 'year': self.year, 'views': self.views })

api = Api(app)

video_put_parser = reqparse.RequestParser()
video_put_parser.add_argument('title', type=str, required=True, help='Title cannot be blank!')
video_put_parser.add_argument('year', type=int, required=True, help='Year cannot be blank!')
video_put_parser.add_argument('views', type=int, required=False, help='Views must be of type integer!')

resource_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'year': fields.Integer,
    'views': fields.Integer
}

def abort_if_video_doesnt_exist(video_id):
    video = VideoModel.query.get(video_id)
    if video is None:
        abort(404, message="Video with id of {} doesn't exist".format(video_id))
        
def abort_if_video_exists(title, year):
    video = VideoModel.query.filter_by(title=title, year=year).first()
    if video is not None:
        abort(400, message="Video with title '{}' published in year {} already exists".format(title, year))
        
class VideoListResource(Resource):
    @marshal_with(resource_fields)
    def get(self):
        return VideoModel.query.all(), 200  
   
    @marshal_with(resource_fields) 
    def post(self):
        new_video_args = video_put_parser.parse_args()
        abort_if_video_exists(new_video_args['title'], new_video_args['year'])
        new_video = VideoModel(title=new_video_args['title'], year=new_video_args['year'], views=new_video_args.get('views', 0))
        db.session.add(new_video)
        db.session.commit()
        
        return new_video, 201
        

class VideoResource(Resource):
    @marshal_with(resource_fields)
    def get(self, video_id):
        video = VideoModel.query.get(video_id)
        if video is not None:
            return video, 200 
        abort(404, description="Video not found")
        
    @marshal_with(resource_fields)
    def put(self, video_id):
        abort_if_video_doesnt_exist(video_id)
        args = video_put_parser.parse_args()
        video = VideoModel.query.filter_by(id=video_id)
        video.update({'title': args['title'], 'year': args['year'], 'views': args['views']})
        db.session.commit()
        return video.first(), 201
        
    def delete(self, video_id):
        abort_if_video_doesnt_exist(video_id)
        video = VideoModel.query.get(video_id)
        db.session.delete(video)
        db.session.commit()
        return '', 204

api.add_resource(VideoResource, '/videos/<int:video_id>')
api.add_resource(VideoListResource, '/videos')

def seed_db(db, VideoModel):
    print("Creating database and adding sample data...")
    db.drop_all()
    db.create_all()
    db.session.add(VideoModel(title='The mighty ducks', year=1993, views=1200))
    db.session.commit()

if __name__ == 'app':
    print("Starting app...")        
    with app.app_context():
        seed_db(db, VideoModel) 
    app.run(debug=True)
