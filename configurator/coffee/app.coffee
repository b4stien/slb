class Utils
  buildConfig: () ->
    config = {}
    config['name'] = $('#cfg-config-name').val()

    config['type'] = $('#cfg-config-type').val()
    if config['type'] == 'date'
      config['date'] = $('#cfg-config-date').val()

    config['generatedTimestamp'] = $('#cfg-config-timestamp').val()

    config['families'] = []

    _.each window.families, (family) ->
      config['families'].push family.buildConfig()

    return config

  isValidConfig: (config) ->
    mandatoryProperties = ['name', 'generatedTimestamp', 'type', 'families']
    for prop in mandatoryProperties
      if not _.has config, prop
        return false

    types = ['serialNumbers', 'date']
    if config['type'] not in types
      return false

    if not _.isArray config['families']
      return false

    if config['type'] == 'serialNumbers'
      for family in config['families']
        if not _.isObject family
          return false

        mandatoryFamilyProperties = ['name', 'serialNumbers', 'orderedTests']
        for prop in mandatoryFamilyProperties
          if not _.has family, prop
            return false

        if not _.isArray family['serialNumbers']
          return false

        if not _.isArray family['orderedTests']
          return false

        for test in family['orderedTests']
          if not _.isObject test
            return false

          mandatoryTestProperties = ['name', 'id']
          for prop in mandatoryTestProperties
            if not _.has test, prop
              return false

    else if config['type'] == 'dates'
      return false

    return true

Utils = new Utils()
