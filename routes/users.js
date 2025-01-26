const express = require('express')
const usersController = require('../controllers/users.controller')
const auth = require('../middleware/auth')

const router = express.Router()

router.post("/change-name", auth.authCheck, usersController.changeName)
router.post("/change-password", auth.authCheck, usersController.changePassword)
router.post("/sign-up",auth.authCheck, usersController.signUp)
router.post("/login", usersController.login)

module.exports = router