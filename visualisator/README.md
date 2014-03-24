## Configuration

The config is done in a file named `visualisatorConfig.json`, which has
to be in the root directory, next to index.html.

Four settings are expected in this file, described in
visualisatorConfig.sample.json. Be careful, as comments are forbidden in
JSON syntax, this config file is not valid.

All the pathes in this directory are relative to the root directory (ie
where index.html lives).

Test colours can be customized in `css/visualisator.css`. A test with
the status `RandomStatus` will have the class `test-randomstatus`.

## Utilisation

Once the config is done, simply open `index.html`.

## Known limitation : XHR on filesystem

Due to how the data are fetched, the interface may need special
permission. More precisely, the browser running the interface must be
able to perform XHR requests against the filesystem.

Firefox is known to work out of the box with these requests.

A good way to bypass this requirement could be to dynamically inject
well conceived JS scripts into the html's head à la JSONP.

## Development

Some parts of the application are written in "raw" JavaScript, and other
are written in CoffeeScript (which has then to be translated into JS).

To ease the process, one could use Grunt. Some simple steps would be:

    npm install -g grunt-cli  # Globaly installs grunt-cli
    npm install               # Locally installs dependencies (cf package.json)
    grunt                     # Runs Grunt default command (cf Gruntfile.js)
