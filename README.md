# What is this?

It is a special session store written for use in Django. The purpose of this special session store is to write the sessions to the Redis server by default, but continue to save to MongoDB when there is a problem with the Redis server.

## Installation

These codes are;
```bash
python: 3.8,
django: 3.1.4
```
written with.


## Usage

- Locate the relevant files somewhere in your django project.

- The SESSION_ENGINE section in the project's settings should be updated.

Example SESSION_ENGINE;
```bash
SESSION_ENGINE = 'general.utility.sessionStore'
```
## License

[MIT](https://choosealicense.com/licenses/mit/)