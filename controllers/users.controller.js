const models = require("../models");
const bcryptjs = require("bcryptjs");
const jwt = require("jsonwebtoken");
const fastestValidator = require("fastest-validator");
const dotenv = require("dotenv");

dotenv.config();

// Update name
const changeName = (req, res) => {
    // Step 1: Verify user exists by ID
    models.User.findByPk(req.body.userId)
        .then(result => {
            if (!result) {
                return res.status(404).json({ message: "User not found!" });
            }

            // Step 2: Compare current password
            bcryptjs.compare(req.body.currentPassword, result.password, function(err, isMatch) {
                if (err) {
                    console.error("Password Compare Error:", err);
                    return res.status(500).json({ message: "Password comparison failed!" });
                }

                if (!isMatch) {
                    return res.status(401).json({ message: "Incorrect current password!" });
                }

                // Step 3: Update the user's name (if password is correct)
                result.update({ name: req.body.newName })
                    .then(() => {
                        res.status(200).json({ message: "Name updated successfully!" });
                    })
                    .catch(updateError => {
                        console.error("Update Name Error:", updateError);
                        res.status(500).json({ message: "Error updating name", errors: updateError });
                    });
            });
        })
        .catch(error => {
            console.error("Database Error (FindByPk):", error);
            res.status(500).json({ message: "Something went wrong while fetching user", errors: error });
        });
};


//update-password
const changePassword = (req, res) => {
    // Step 1: Verify user exists by ID
    models.User.findByPk(req.body.userId).then(user => {
        if (!user) {
            return res.status(404).json({ message: "User not found!" });
        }

        // Step 2: Compare current password
        bcryptjs.compare(req.body.currentPassword, user.password, function(err, isMatch) {
            if (err) {
                console.error("Password Compare Error:", err);
                return res.status(500).json({ message: "Password comparison failed!" });
            }

            if (!isMatch) {
                return res.status(401).json({ message: "Incorrect current password!" });
            }

            // Step 3: Hash and update the new password
            bcryptjs.genSalt(10, function(err, salt) {
                if (err) {
                    console.error("Salt Generation Error:", err);
                    return res.status(500).json({ message: "Failed to update password!" });
                }

                bcryptjs.hash(req.body.newPassword, salt, function(err, hash) {
                    if (err) {
                        console.error("Hashing Error:", err);
                        return res.status(500).json({ message: "Failed to update password!" });
                    }

                    // Update the password in the database
                    user.update({ password: hash }).then(() => {
                        res.status(200).json({ message: "Password updated successfully!" });
                    }).catch(error => {
                        console.error("Database Error (Update):", error);
                        res.status(500).json({ message: "Failed to update password!" });
                    });
                });
            });
        });
    }).catch(error => {
        console.error("Database Error (FindByPk):", error);
        res.status(500).json({ message: "Something went wrong!", errors: error });
    });
};


//sign-up
const signUp = (req, res) => {
  // Debug: Check incoming request body
  console.log("Request Body:", req.body);

  models.User.findOne({ where: { username: req.body.username } })
    .then((result) => {
      if (result) {
        return res.status(409).json({
          message: "Username has already been taken",
        });
      } else {
        bcryptjs.genSalt(10, function (err, salt) {
          if (err) {
            console.error("Salt Error:", err);
            return res
              .status(500)
              .json({ message: "Password encryption failed" });
          }

          bcryptjs.hash(req.body.password, salt, function (err, hash) {
            if (err) {
              console.error("Hash Error:", err);
              return res
                .status(500)
                .json({ message: "Password encryption failed" });
            }

            const user = {
              name: req.body.name,
              username: req.body.username,
              password: hash,
            };

            const schema = {
              name: { type: "string", optional: false, max: 100 },
              username: { type: "string", optional: false, max: 100 },
              password: { type: "string", optional: false, min: 8, max: 100 },
            };

            const validator = new fastestValidator();
            const validationResponse = validator.validate(user, schema);

            if (validationResponse !== true) {
              console.error("Validation Errors:", validationResponse);
              return res.status(400).json({
                message: "Validation failed",
                errors: validationResponse,
              });
            }

            models.User.create(user)
              .then((result) => {
                res.status(201).json({
                  message: "User created successfully",
                });
              })
              .catch((error) => {
                console.error("Database Error (Create):", error);
                res.status(500).json({
                  message: "Something went wrong!",
                  errors: error,
                });
              });
          });
        });
      }
    })
    .catch((error) => {
      console.error("Database Error (FindOne):", error);
      res.status(500).json({
        message: "Something went wrong!",
        errors: error,
      });
    });
};

//login
const login = (req, res) => {
  models.User.findOne({ where: { username: req.body.username } })
    .then((user) => {
      if (user === null) {
        res.status(401).json({
          message: "Invalid credentials!",
        });
      } else {
        bcryptjs.compare(
          req.body.password,
          user.password,
          function (err, result) {
            if (result) {
              const token = jwt.sign(
                {
                  name: user.name,
                  username: user.username,
                  userId: user.id,
                },
                process.env.JWT_KEY,
                { expiresIn: "1h" },
                function (err, token) {
                  res.status(200).json({
                    message: "Authentication succeeded!",
                    token: token,
                  });
                }
              );
            } else {
              res.status(401).json({
                message: "Invalid credentials!",
              });
            }
          }
        );
      }
    })
    .catch((error) => {
      res.status(500).json({
        message: "Something went wrong!",
        errors: error,
      });
    });
};

module.exports = {
  signUp: signUp,
  login: login,
  changePassword: changePassword,
  changeName: changeName
};
