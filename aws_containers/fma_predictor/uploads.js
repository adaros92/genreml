// modules I either use or might like to
const express = require('express');
const app = express();;
const logger = require('morgan');
const bodyParser = require('body-parser');
const https = require('https')
// flip this variable to turn off most console logging
const global_debug = true;
// create application/json parser
const jsonParser = bodyParser.json();
// parser for urlencoding
const urlencodedParser = bodyParser.urlencoded({ extended: false });
const fs = require('fs');

//Probably from stack overflow but I've been using this for ages, so who knows.
guid = function() {
   function s4() {
       return Math.floor((1 + Math.random()) * 0x10000)
       .toString(16)
       .substring(1);
   }
   return s4() + s4() + s4() + s4() +
   s4() + s4() + s4() + s4();
}

// variables for publicly accessable bind
var serverBinding = "0.0.0.0"

//this is testing code
app.get('/test',function(req, res){
    res.send("server up");
});

// this is where uploaded files get written to disk
// https://code.tutsplus.com/tutorials/file-upload-with-multer-in-node--cms-32088
const multer = require('multer');
// SET STORAGE
// implements writing to disk using the multer package.
// allows uploading single or multiple files
var storage = multer.diskStorage({
  destination: function (req, file, cb){
      cb(null, '/opt/temp_model_uploads/');
  },
  filename: function (req, file, cb) {
    cb(null, guid()+".dat");
  }
});
// set up the multer package to handle file uploads
var upload = multer({ storage: storage })
//Uploading multiple files
app.post('/nodemodeluploads', upload.array('model', 12), (req, res, next) => {
  const files = req.files;
  if (!files) {
    res.send({"message":"please upload a file."})
  }else{
    // then redirect client back to mainpage where they can search for the uploaded music or continue other tasks
    res.send({
        "message":"file uploaded!",
        "uploaded": true
    })
  }
});

const PORT_VAR = 8080;
const SERVER_BINDING = '0.0.0.0';

app.listen(PORT_VAR, SERVER_BINDING, (err) => {
 if( err ) {
    // something went wrong
     console.log(err);
 } else {
   // looks like were all good here
     console.log('\nServer up!');
 }
});
