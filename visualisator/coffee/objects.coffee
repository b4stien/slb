class Family extends Backbone.Model

  initialize: () ->
    @tools = new Backbone.Collection()


class Tool extends Backbone.Model

  initialize: () ->
    @logs = []

  insertLog: (log) ->
    @logs.splice _.sortedIndex(@logs, log, (log) -> log.timestamp), 0, log

  parseMat: (rawMat) ->
    mat =
      'type': 'mat'
      'timestamp': rawMat[0]
      'testID': rawMat[3]
      'status': rawMat[4]
      'rawLog': rawMat
    if rawMat[5]
      mat['tfl'] = rawMat[5]
    @insertLog mat

  parseTfl: (rawTfl) ->
    tfl =
      'type': 'tfl'
      'timestamp': rawTfl[0]
      'testID': rawTfl[3]
      'rawLog': rawTfl
    @insertLog tfl

  getToolTest: (testID) ->
    new ToolTest @, testID

  _lastDate: (testID) ->
    testLogs = _.filter @logs, (log) -> log.testID == testID
    if _.last(testLogs)
      return moment _.last(testLogs).timestamp, 'X'
    return undefined

  _lastMat: (testID) ->
    testMats = _.filter @logs, (log) -> (log.testID == testID and log.type == 'mat')
    if _.last(testMats)
      return _.last(testMats)
    return undefined


class ToolTest

  constructor: (tool, testID) ->
    @tool = tool
    @testID = testID

  lastDate: () ->
    @tool._lastDate(@testID)

  lastMat: () ->
    @tool._lastMat(@testID)

  status: () ->
    if @lastMat()
      return 'test-' + @lastMat().status.toLowerCase()
    return ''
