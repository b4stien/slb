class Family extends Backbone.Model

  initialize: () ->
    @set 'name', ''
    @set 'tools', []
    @set 'tests', []

  buildConfig: () ->
    config = {}

    config['name'] = @get('name')
    config['serialNumbers'] = @get('tools')
    config['orderedTestIDs'] = @get('tests')

    return config
