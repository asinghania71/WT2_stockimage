import numpy as np
import re
from flask_api import status
from datetime import datetime
import os
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import tflite_runtime.interpreter as tflite
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./static"
app.config['MODEL_FOLDER'] = "d:/AngularCourse/stockphotobackend/coco"


interpreter = tflite.Interpreter(model_path=os.path.join(app.config['MODEL_FOLDER'], "detect.tflite"))
interpreter.allocate_tensors()
_, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']

# print(input_details)


# print(output_details)
def load_labels():
  """Loads the labels file. Supports files with or without index numbers."""
  with open(os.path.join(app.config['MODEL_FOLDER'], "labelmap.txt"), 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels
labels=load_labels()
def set_input_tensor(image):
  """Sets the input tensor."""
  global interpreter
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image

def get_output_tensor(index):
  global interpreter
  
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  
  return tensor

def detect_objects(image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""
  global interpreter

  set_input_tensor(image)
  interpreter.invoke()

  # Get all output details
  boxes = get_output_tensor( 0)
  classes = get_output_tensor( 1)
  scores = get_output_tensor( 2)
  count = int(get_output_tensor( 3))

  results = []
  for i in range(count):
    if scores[i] >= threshold:
     try: 
      result = {
          'bounding_box': boxes[i],
          'class_id': labels[classes[i]],
          'score': scores[i]
      }

      results.append(result)
     except:
      continue
  return results


CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test2.db'
db = SQLAlchemy(app)
# Ensure FOREIGN KEY for sqlite3
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    def _fk_pragma_on_connect(dbapi_con, con_record):  # noqa
        dbapi_con.execute('pragma foreign_keys=ON')

    with app.app_context():
        from sqlalchemy import event
        event.listen(db.engine, 'connect', _fk_pragma_on_connect)
# app.run(debug=True)
#dictionary containing book names
# and quantities
imgno=0
class User(db.Model):
	username = db.Column(db.Text(), unique=True, primary_key=True)
	password = db.Column(db.Text(), nullable=False)
	#ride= db.relationship("Ride", back_populates="user")

	def __repr__(self):
		return '<User %r>' % self.username
	def __init__(self, Name,passw):
		self.username = Name
		self.password= passw

class Img(db.Model):
	imgId = db.Column(db.Integer,primary_key=True)
	path = db.Column(db.Text(),nullable=False)
	# created_by= db.Column(db.Text(),db.ForeignKey('user.username'),nullable=False)
	# price=db.Column(db.Integer,primary_key=True)
	tags=db.Column(db.Text())
	#user= db.relationship("User",back_populates="ride")
#db foreign Key contrain to be added
	def __repr__(self):
		return '<image %r>' % self.imgId
	def __init__(self,p,t):
		self.path= p
		# self.created_by= c
		# self.price= pr
		self.tags=t
# class Ridetake(db.Model):
# 	rideId = db.Column(db.Integer,db.ForeignKey('ride.rideId'),nullable=False, primary_key=True)
# 	user=db.Column(db.Text(),db.ForeignKey('user.username'),nullable=False, primary_key=True)
# 	def __repr__(self):
# 		return '<rideId %r>' % self.rideId
# 	def __init__(self,r,u):
# 		self.rideId= r
# 		self.user= u
		

@app.route("/api/v1/db/write",methods=["POST"])
def write_db(db=db):
#“column name” : “data”,
#“column” : “column name”,
#“table” : “table name”
	# print(request.get_json())
	l=request.get_json()['insert']
	me =("global us;us="+request.get_json()["table"]+"("+ str(l)[1:-1]+")")
	# print(type(me))
	exec(me)	
	# print(us)
	#User("a","b")
	db.session.add(us)
	db.session.commit()
	return (jsonify())


@app.route("/api/v1/db/read",methods=["POST"])
def read_db():
# 	{
# “table”: “table name”,
# “columns”: [“column name”,],
# “where”: “[column=='value', 
	try:
		me =("global us;us="+request.get_json()["table"]+".query.filter"+"("+request.get_json()["where"]+").all()")
	except:
 		me =("global us;us="+request.get_json()["table"]+".query.all()")
	# print(me)
	exec(me)
	# print(us)
	lis=[]
	for i in us:
		global res
		res={}
		for j in request.get_json()["columns"]:
			exec("res[j]=i."+j)
		lis+=[res]
	# print()
	return (jsonify(lis))

	# db.session.add(me)
	# db.session.commit()
@app.route("/api/v1/users",methods=["PUT"])
def create_user():
	#try:
		ur=request.url_root
		#IF SHA1 TO BE DONE case insensitive
		#print(request.get_json()['username'],request.get_json()['password'])
		try:
			data={'table':'User','insert':[request.get_json()['username'],request.get_json()['password']]}
		except:
			return ("Invalid Request",status.HTTP_400_BAD_REQUEST)
		# print(data)
		r=requests.post(ur+'api/v1/db/write',json=data )
		# print(r.status_code)
		if r.status_code==500:
			return ("Not Unique Username",status.HTTP_400_BAD_REQUEST)
		return (jsonify(),status.HTTP_201_CREATED)	
	# except:
	# 	abort(400)
@app.route("/api/v1/img",methods=["POST"])
def upload_img():
	#try:
		ur=request.url_root
		# #datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
		# #print(request.gset_json()['username'],request.get_json()['password'])
		# try:
		# 	data={'table':'Ride','insert':[request.get_json()['source'],request.get_json()['destination'],request.get_json()['timestamp'],request.get_json()['created_by']]}
		# except:
		# 	return ("Invalid Request",status.HTTP_400_BAD_REQUEST)
			

		# # print(data)
		global imgno
		filepath=""
		# #print(r.status_code)
		# if r.status_code==500:
		# 	return ("User Not Found",status.HTTP_400_BAD_REQUEST)
		if 'image' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['image']
		ext=file.filename.split(".")[1].lower()
		if ext in ['jpg','png','jpeg','gif']:
			imgno+=1
			filename = secure_filename("img"+str(imgno)+"."+ext)
			filepath=app.config['UPLOAD_FOLDER']+"/img"+str(imgno)+"."+ext
			
			file.save(filepath)
			filepath="http://localhost:5000/static"+"/img"+str(imgno)+"."+ext
		else:
			return (jsonify(),status.HTTP_400_BAD_REQUEST)
		image = Image.open((os.path.join(app.config['UPLOAD_FOLDER'], filename))).convert('RGB').resize((input_width, input_height), Image.ANTIALIAS)
		
		results = detect_objects(image, 0.4)
		print("****************************")
		print(results)
		print("****************************")
		classd=[]
		for i in results:
			classd+=[i['class_id']]

		# ??try:
		data={'table':'Img','insert':[filepath,' '.join([str(elem) for elem in list(set(classd))])] }
		r=requests.post(ur+'api/v1/db/write',json=data )
		
		# except:
			# return ("Invalid Request",status.HTTP_400_BAD_REQUEST)
		
		return (jsonify(list(set(classd))),status.HTTP_201_CREATED)

	#except:
	#	abort(400)

	#
	# me = exec(request.get_json()["table"]+"("+request.get_json()["table"]+")")
	# db.session.add(me)
	# db.session.commit()
@app.route("/api/v1/img",methods=["GET"])
def get_image():
	#try:	
		ur=request.url_root
		#datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
		# print(request.gset_json()['username'],request.get_json()['password'])
		# print(request.args.get('source'))
		data={"table": "Img","columns": ["path","tags"]}
			# print(data)
		r=requests.post(ur+'api/v1/db/read',json=data )

		d=r.json()
		
		return (jsonify(d))	

		#except:
	#	abort(400)

	#
	# me = exec(request.get_json()["table"]+"("+request.get_json()["table"]+")")
	# db.session.add(me)
	# db.session.commit()
	

# @app.route("/api/v1/rides/<rideId>",methods=["POST"])
# def join_rides(rideId):
# 		ur=request.url_root
# 		#datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
# 		#print(request.gset_json()['username'],request.get_json()['password'])
# 		try:
# 			data={'table':'Ridetake','insert':[rideId,request.get_json()['username']]}
# 			# print(data)
# 		except:
# 			return ('Missing Parameter',status.HTTP_400_BAD_REQUEST)
		
# 		r=requests.post(ur+'api/v1/db/write',json=data )
		
# 		# print(r.status_code)
# 		if r.status_code==500:
# 			return ("User/Ride Not Found",status.HTTP_400_BAD_REQUEST)
# 		return (jsonify())	
# 	#except:
# 	#	abort(400)
# @app.route("/api/v1/rides/<rideId>")
# def ride_detail(rideId):
# 	#try:
# 		ur=request.url_root
# 		try:
# 			data={"table": "Ride","columns": ["created_by","rideId","timestamp","source","destination"],"where": "Ride.rideId=="+rideId}
# 			# print(data)
# 		except:
# 			return ('Missing Parameter',status.HTTP_400_BAD_REQUEST)
# 		r=requests.post(ur+'api/v1/db/read',json=data )
# 		d=r.json()[0]
# 		d['timestamp'] = datetime.strptime(d['timestamp'], '%a, %d %b %Y %H:%M:%S %Z').strftime('%d-%m-%Y:%S-%M-%H')

# 		data={"table": "Ridetake","columns": ["user"],"where": "Ride.rideId=="+rideId}
# 		# print(data)
# 		r=requests.post(ur+'api/v1/db/read',json=data )
# 		user=(r.json())
# 		d["users"]=[x["user"] for x in user ]

# 		if r.status_code==500:
# 			return ("Ride Not Found",status.HTTP_400_BAD_REQUEST)
		
# 		return (jsonify(d))	
# 	#except:
# 	#	abort(400)

# 	#
# 	# me = exec(request.get_json()["table"]+"("+request.get_json()["table"]+")")
# 	# db.session.add(me)
# 	# db.session.commit()

# @app.route("/api/v1/users/<username>",methods=["DELETE"])
# def del_user(username):
# 	#try:
# 		# ur=request.url_root
# 		# #datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
# 		# #print(request.gset_json()['username'],request.get_json()['password'])
# 		# # print(request.args.get('source'))
# 		# data={"table": "User","columns": ["username","password"],"where": "User.username=='"+username+"'"}
# 		# print(data)
# 		# r=requests.post(ur+'api/v1/db/read',json=data )
# 		# d=r.json()
# 		# for i in d:
# 		# 		o=User(i['username'],i['password'])
# 		# 		db.session.delete(o)
# 		# db.session.commit()
# 		# return (jsonify())	
# 	#except:
# 	#	abort(400)

# 	#
# 	# me = exec(request.get_json()["table"]+"("+request.get_json()["table"]+")")
# 	# db.session.add(me)
# 	# db.session.commit()
# 	a=User.query.filter(User.username==username).first()
# 	print(a)
# 	if(a==None):
# 		return('Username Not found',status.HTTP_400_BAD_REQUEST)
# 	db.session.delete(a)
# 	db.session.commit()	
# 	return(jsonify())

# @app.route("/api/v1/rides/<rideId>",methods=["DELETE"])
# def del_ride(rideId):
# 	#try:
# 		# ur=request.url_root
# 		#datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
# 		#print(request.gset_json()['username'],request.get_json()['password'])
# 		# print(request.args.get('source'))
# 		# data={"table": "Ride","columns":["created_by","rideId","timestamp","source","destination"],"where": "Ride.rideId=="+rideId}
# 		# print(data)
# 		# r=requests.post(ur+'api/v1/db/read',json=data )
# 		# print(r)
# 		# d=r.json()
# 		# for i in d:
# 		# 		o=Ride(i['rideId'],i['source'],i['destination'],i['timestamp'],i['created_by'])		
# 		# 		db.session.delete(o)
# 		# db.session.commit()
# 		# return (jsonify())	
# 	#except:
# 	#	abort(400)

# 	#
# 	# me = exec(request.get_json()["table"]+"("+request.get_json()["table"]+")")
# 	# db.session.add(me)
# 	# db.session.commit()
# 	b=Ride.query.filter(Ride.rideId==rideId).first()
# 	if(b==None):
# 		return('Username Not found',status.HTTP_400_BAD_REQUEST)
	
# 	# ?print(b)
# 	db.session.delete(b)
# 	db.session.commit()	
# 	return(jsonify())
	


if __name__ == '__main__':	
	app.debug=True
