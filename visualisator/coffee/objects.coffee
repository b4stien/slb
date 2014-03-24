class Family extends Backbone.Model

  initialize: () ->
    @tools = new Backbone.Collection()


class Tool extends Backbone.Model

  initialize: () ->
    @logs = []

  insertLog: (log) ->
    duplicate = _.find(@logs, (otherLog) -> JSON.stringify(log) == JSON.stringify(otherLog))
    if duplicate
      return

    @logs.splice _.sortedIndex(@logs, log, (log) -> log.timestamp), 0, log
    @trigger 'change'

  addRedo: (testID, timestamp) ->
    redo =
      'type': 'redo'
      'timestamp': timestamp
      'testID': testID
    @insertLog mat

  parseMat: (rawMat) ->
    mat =
      'type': 'mat'
      'timestamp': parseInt(rawMat[0])
      'testID': rawMat[3]
      'status': rawMat[4]
      'rawLog': rawMat
    if rawMat[5]
      mat['tfl'] = rawMat[5]
    @insertLog mat

  parseTfl: (rawTfl) ->
    tfl =
      'type': 'tfl'
      'timestamp': parseInt(rawTfl[0])
      'testID': rawTfl[3]
      'redo': rawTfl[5]
      'rawLog': rawTfl

    if tfl.redo
      console.log 'redo !'
      console.log tfl.redo

      testIDs = Utils.parseRedo tfl.redo
      _.each testIDs, (testID) =>
        @addRedo testID, tfl.timestamp

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
