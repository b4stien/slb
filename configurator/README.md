## Configuration & Utilisation

No configuration needs to be done to use this application. Simply open
`index.html`.

## Development

Some parts of the application are written in "raw" JavaScript, and other
are written in CoffeeScript (which has then to be translated into JS).

To ease the process, one could use Grunt. Some simple steps would be:

    npm install -g grunt-cli  # Globaly installs grunt-cli
    npm install               # Locally installs dependencies (cf package.json)
    grunt                     # Runs Grunt default command (cf Gruntfile.js)
