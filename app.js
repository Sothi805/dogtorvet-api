const express = require('express')
const bodyParser = require('body-parser')
const cors = require('cors')

const usersRouter = require('./routes/users')
const imageRouter = require('./routes/image')

const app = express()

app.use(cors(
    {
        origin: 'http://localhost:5173', // Allow only your frontend
        methods: 'GET,POST,PUT,DELETE', // Allow specific methods
        credentials: true, // Include credentials (if needed)
    }
));

app.get('/', (req, res) => {
    res.send("API started");
})


app.use(bodyParser.json())
app.use("/users", usersRouter)
app.use('/images', imageRouter)


module.exports = app
