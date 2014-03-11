class Family extends Backbone.Model

  initialize: () ->
    @tools = new Backbone.Collection()


class Tool extends Backbone.Model

  initialize: () ->
    @logs = []

  lastDate: (testID) ->
    testLogs = _.filter @logs, (log) -> log.testID == testID
    if _.last(testLogs)
      return moment _.last(testLogs).timestamp, 'X'
    return undefined

  insertLog: (log) ->
    @logs.splice _.sortedIndex(@logs, log, (log) -> log.timestamp), 0, log

  parseMat: (rawMat) ->
    mat =
      'type': 'mat'
      'timestamp': rawMat[0]
      'testID': rawMat[3]
      'rawLog': rawMat
    @insertLog mat

  parseTfl: (rawTfl) ->
    tfl =
      'type': 'tfl'
      'timestamp': rawTfl[0]
      'testID': rawTfl[3]
      'rawLog': rawTfl
    @insertLog tfl
