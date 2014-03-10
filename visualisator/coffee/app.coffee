class Utils
  getJSONFile: (fileURL) ->
    xhr = new XMLHttpRequest()
    xhr.open 'GET', fileURL, false
    xhr.overrideMimeType 'application/json'
    xhr.send null
    JSON.parse xhr.responseText

  CSVToArray = (csvString) ->
    result = []

    _.each csvString.split('\n'), (csvLine) ->
      resultLine = [];
      resultLine.rawLine = csvLine;

      if csvLine.trim() == ''
        return

      _.each csvLine.split(','), (csvItem) ->
        resultLine.push csvItem.trim()

      result.push resultLine

    result

  getCSVFile: (fileURL) ->
    xhr = new XMLHttpRequest()
    xhr.open 'GET', fileURL, false
    xhr.overrideMimeType 'text/csv'
    xhr.send null
    CSVToArray xhr.responseText

Utils = new Utils()
