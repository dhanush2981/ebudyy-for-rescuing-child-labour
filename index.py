from flask import Flask, render_template, request,flash
import pandas as pd
import csv
from DBConnection import DBConnection
import re
from flask import session
from werkzeug.utils import secure_filename
#from ChildIdentification import predict,show_prediction_labels_on_image,train
from detect import age_gen_detect
import sys
import os
from PIL import Image
import io
import base64
import shutil
from random import randint
import numpy as np

app = Flask(__name__)
app.secret_key = "abc"

@app.route('/')
def index():
    return render_template('index.html')

#NGO SECTION

@app.route("/ngo")
def ngo():
    return render_template("ngo.html")

@app.route("/ngologin",methods =["GET", "POST"])
def ngologin():
    uid = request.form.get("unm")
    pwd = request.form.get("pwd")
    if uid=="ngo" and pwd=="ngo":
        return render_template("ngohome.html")
    else:
        return render_template("ngo.html",msg="Invalid Credentials")

@app.route("/ngo_home")
def ngo_home():
    return render_template("ngohome.html")

@app.route("/complaints")
def complaints():
    try:
        database = DBConnection.getConnection()
        cursor = database.cursor()
        cursor.execute("SELECT *FROM uploadphotos")
        rows = cursor.fetchall()

    except Exception as e:
        print("Error=" + e.args[0])
        tb = sys.exc_info()[2]
        print(tb.tb_lineno)

    return render_template("complaints.html",rawdata=rows)

@app.route("/update/<sno>")
def update(sno):
    database = DBConnection.getConnection()
    cursor = database.cursor()
    cursor.execute("SELECT * FROM uploadphotos where sno='" + sno + "' ")
    rows = cursor.fetchall()
    print(rows)
    return render_template("update.html",detailes=rows)

@app.route("/update2",methods =["GET", "POST"])
def update2():
    sno = request.form["sno"]
    print(sno)
    sts = request.form.get('status')
    print("status:", sts)
    database = DBConnection.getConnection()
    cursor = database.cursor()
    #qry = "update uploadphotos set status='" + status + "' where sno= '" + sno + " ' "
    cursor.execute("UPDATE uploadphotos set status='" + sts + "' where sno= '" + sno + " ' ")
    database.commit()

    return render_template("ngohome.html",messages="Staus Updated successfully")


#USERS SECTION

@app.route("/users")
def users():
    return render_template("user.html")

@app.route("/user_reg")
def user_reg():
    return render_template("user_reg.html")

@app.route("/user_reg2",methods =["GET", "POST"])
def user_reg2():
    name = request.form.get('name')
    uid = request.form.get('uid')
    pswd = request.form.get('pwd')
    email = request.form.get('email')
    mno = request.form.get('mno')
    database = DBConnection.getConnection()
    cursor = database.cursor()
    sql = "select count(*) from users where uid=' " + uid + " ' "
    cursor.execute(sql)
    res = cursor.fetchone()[0]
    #print("number of",res)
    if res > 0:
        return render_template("register.html", msg="already exists..!")
    else:
        qry = "insert into users(name,uid,pwd,email,mno) values  (%s,%s,%s,%s,%s)"
        values=(name,uid,pswd,email,mno)
        cursor.execute(qry,values)
        database.commit()
        return render_template("user.html",msg="added")
    return ""

@app.route("/userlogin",methods =["GET", "POST"])
def userlogin():
        uid = request.form.get("unm")
        pwd = request.form.get("pwd")
        database = DBConnection.getConnection()
        cursor = database.cursor()
        sql = "select count(*) from users where uid='" + uid + "' and pwd='" + pwd + "'"
        cursor.execute(sql)
        res = cursor.fetchone()[0]
        if res > 0:
            session['uid'] = uid
            qry = "select * from users where uid= '" + uid + " ' "
            cursor.execute(qry)
            val = cursor.fetchall()
            for values in val:
                name = values[0]
                #print(name)
            return render_template("userhome.html",name=name)
        else:
            return render_template("user.html",msg="Invalid Credentials")

        return render_template("admin.html")

@app.route("/user_home")
def user_home():
    database = DBConnection.getConnection()
    cursor = database.cursor()
    uid = session['uid']
    qry = "select * from users where uid= '" + uid + " ' "
    cursor.execute(qry)
    val = cursor.fetchall()
    for values in val:
        name = values[0]

    return render_template("userhome.html",name=name)

@app.route("/uupload_photo")
def uupload_photo():
    return render_template("user_upload_photo.html")

@app.route("/uupload_photo2",methods =["GET", "POST"])
def uupload_photo2():
    try:
        uid=session['uid']
        database = DBConnection.getConnection()
        cursor = database.cursor()
        sql = "select * from users where uid='" + uid + "' "
        cursor.execute(sql)
        res = cursor.fetchall()
        print(res)
        for values in res:
            name=values[0]
            number=values[4]
            print(name)
            print(number)

        adrs = request.form.get('adrs')
        image = request.files['file']
        print("image:",image)
        imgdata = secure_filename(image.filename)
        print("imgdata:",imgdata)

        filename = image.filename
        filelist = [f for f in os.listdir("testimg")]
        for f in filelist:
            os.remove(os.path.join("testimg", f))
        image.save(os.path.join("testimg", imgdata))
        image_path = "../rescue_child_labour/testimg/" + filename
        result = list(age_gen_detect(image_path))
        #result2=list(result)
        print("gen&age",result)
        gender=result[0]
        age=result[1]
        new_image = str(randint(1000, 9999)) + ".jpg"

        with open("../rescue_child_labour/testimg/" + filename, 'rb') as image_file:
            image_string = image_file.read()
            with open("../rescue_child_labour/static/" + new_image, 'wb') as dest_image:
                dest_image.write(image_string)

        database = DBConnection.getConnection()
        cursor = database.cursor()
        query = "insert into uploadphotos(name,number,address,photo,gender,age,status) values(%s,%s,%s,%s,%s,%s,%s)"
        values = (name,number,adrs, new_image,gender,age,'wait')
        cursor.execute(query, values)
        database.commit()

        #return render_template("user_upload_photo.html",message="Photo Uploaded Successfully..!")

        return render_template("user_upload_photo.html",message="Photo Uploaded Successfully..!")

    except Exception as e:
           print(e)

@app.route('/user_status_cheeck')
def user_status_cheeck():
    uid = session['uid']
    database = DBConnection.getConnection()
    cursor = database.cursor()
    sql = "select * from users where uid='" + uid + "' "
    cursor.execute(sql)
    detailes=cursor.fetchall()
    print("detailes",detailes)
    for values in detailes:
        name=values[0]
        print(name)

    database = DBConnection.getConnection()
    cursor = database.cursor()
    cursor.execute("SELECT * FROM uploadphotos where name='" + name + "' ")
    detailes1 = cursor.fetchall()
    print("detailes1", detailes1)

    return render_template("user_status_cheeck.html",detailes1=detailes1)





if __name__ == '__main__':
    app.run(debug=True)