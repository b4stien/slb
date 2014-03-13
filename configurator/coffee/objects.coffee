class Family extends Backbone.Model

  initialize: () ->
    @set 'name', ''
    @set 'tools', []
    @set 'tests', []

  buildConfig: () ->
    config = {}

    config['name'] = @get 'name'
    config['serialNumbers'] = @get 'tools'
    config['orderedTests'] = @get 'tests'

    return config

  parseFamily: (family) ->
    @set 'name', family['name']
    @set 'tools', family['serialNumbers']
    @set 'tests', family['orderedTests']
