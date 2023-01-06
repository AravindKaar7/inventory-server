import os
from typing import List
from fastapi import FastAPI
import uvicorn
import boto3
from fastapi.middleware.cors import CORSMiddleware
from bson.objectid import ObjectId
from pymongo import MongoClient
# from Form import Form
from fastapi import File, UploadFile, Form
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client.powerbi_inventory

SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_KEY = os.getenv('ACCESS_KEY')
S3_BUCKET_BASE_URI = 'https://pbi-assets.s3.ap-south-1.amazonaws.com/dashboards/new_demo/'
S3_UPLOAD_URI = 'dashboards/new_demo/'

s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
bucket = s3.list_objects(Bucket = 'pbi-assets')

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get('/')
async def home():
    global db
    data = []
    coll = db['components-2']
    for i in coll.find({}):
        i['_id'] = str(i['_id'])
        data.append(i)
    return {'message': data}

@app.get('/get/{id}')
async def getProd(id):
    global db
    coll = db['components-2']
    res = coll.find_one({'_id': ObjectId(id)},{'_id':0})
    return {'message': res}

@app.get('/vizprod/{id}')
async def product(id):
    global db
    coll = db.images
    x = coll.find_one({'id': ObjectId(id)},{'_id':0})
    x['id'] = str(x['id'])
    return {'message':x}
@app.get('/viz/group')
async def group():
    global db
    data = []
    coll = db.groups
    coll2 = db['components-2']
    print(coll)
    for i in coll.find({}):
        if coll2.find_one({'desc':i['group']}):
            del i['_id']
            data.append(i)
    return {'message':data}

@app.post('/viz/admin/upload')
async def upload(title:str = Form(), group: str = Form(), desc:str = Form(), logo:str = Form(), files: List[UploadFile] = File()):
    coll_components = db['components-2']
    coll_images = db.images
    groups = []
    coll_groups = db.groups
    for i in coll_groups.find({}):
        del i['_id']
        groups.append(i['group'])
    if group not in groups:
        coll_groups.insert_one({'group':group})
    images = []

    c=0

    for file in files:
        try:
            file_title = file.filename
            s3.upload_fileobj(file.file,'pbi-assets',S3_UPLOAD_URI+file_title)
            file_url = S3_BUCKET_BASE_URI+file_title
            temp = {
                "id":c,
                "title":file_title,
                "src":file_url,
                "desc":""

            }
            images.append(temp)
            c+=1
        except Exception as e:
                print(e)
    try:
        data_comp = {
            "name": title,
            "logo": logo,
            "desc": group,
            "img": images[0]['src'],
            "viewdesc": desc
        }
        ref_id = coll_components.insert_one(data_comp).inserted_id
        print(ref_id)
        data_img = {
            "id":ref_id,
            "urls":images
        }
        img_id = coll_images.insert_one(data_img).inserted_id
        print("img_id",img_id)
    except Exception as e:
        print(e)
    return {'filenames': [i.filename for i in files]}


@app.delete('/viz/admin/delete/{id}')
async def delete(id):
    global db
    coll = db.images
    coll2 = db['components-2']
    try:
        coll2.delete_one({'_id':ObjectId(id)})
        coll.delete_one({'id': ObjectId(id)})
        return {'message':'deleted'}
    except Exception as e:
        print(e)
        return {
            'message':'error'
        }
@app.get('/test')
async def test():
    response = s3.list_buckets()
    for bucket in response['Buckets']:
        print(f' {bucket["Name"]}')
    return 'true'
if __name__ == '__main__':
    uvicorn.run(app)