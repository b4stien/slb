class Family extends Backbone.Model

  initialize: (configType = 'serialNumbers') ->
    @set 'name', ''
    @set 'tools', []

    @set 'configType', configType

    @set 'tests', []

    @set 'serialNumbersPrefix', ''

  buildConfig: () ->
    config = {}

    config['name'] = @get 'name'
    config['orderedTests'] = @get 'tests'

    if @get('configType') == 'serialNumbers'
      config['serialNumbers'] = @get 'tools'

    else if @get('configType') == 'date'
      config['serialNumbersPrefix'] = @get 'serialNumbersPrefix'

    return config

  parseFamily: (family) ->
    @set 'name', family['name']
    @set 'tests', family['orderedTests']
    @set 'configType', family['configType']

    if family['configType'] == 'serialNumbers'
      @set 'tools', family['serialNumbers']

    else if family['configType'] == 'date'
      @set 'serialNumbersPrefix', family['serialNumbersPrefix']

  setConfigType: (configType) ->
    @set 'configType', configType
