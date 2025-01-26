const express = require('express')
const imageController = require('../controllers/image.controller')
const imageUploader = require('../helpers/image-uploader')
const auth = require('../middleware/auth')

const router = express.Router()

router.post('/uploads', auth.authCheck, imageUploader.upload.single('image'), imageController.upload)

module.exports = router