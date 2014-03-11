class Utils
  buildConfig: () ->
    config = {}
    config['name'] = $('#cfg-config-name').val()
    config['generatedTimestamp'] = $('#cfg-config-timestamp').val()

    config['families'] = []

    _.each window.families, (family) ->
      config['families'].push family.buildConfig()

    return config

Utils = new Utils()
