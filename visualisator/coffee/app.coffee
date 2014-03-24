class Utils
  getJSONFile: (fileURL) ->
    xhr = new XMLHttpRequest()
    xhr.open 'GET', fileURL, false
    xhr.overrideMimeType 'application/json'
    xhr.send null
    JSON.parse xhr.responseText

  CSVToArray: (strData, strDelimiter) ->
    strDelimiter = (strDelimiter || ",")
    objPattern = new RegExp("(\\" + strDelimiter + "|\\r?\\n|\\r|^)(?:\"([^\"]*(?:\"\"[^\"]*)*)\"|([^\"\\" + strDelimiter + "\\r\\n]*))", "gi")

    arrData = [[]]
    arrMatches = null

    while (arrMatches = objPattern.exec(strData))
      strMatchedDelimiter = arrMatches[1]

      if strMatchedDelimiter.length && (strMatchedDelimiter != strDelimiter)
        arrData.push([])

      if (arrMatches[2])
        strMatchedValue = arrMatches[2].replace(new RegExp( "\"\"", "g" ), "\"")

      else
        strMatchedValue = arrMatches[3]

      arrData[arrData.length - 1].push(strMatchedValue.trim())

    return arrData

  getCSVFile: (fileURL) ->
    xhr = new XMLHttpRequest()
    xhr.open 'GET', fileURL, false
    xhr.overrideMimeType 'text/csv'
    xhr.send null
    @CSVToArray xhr.responseText, ','

  parseRedo: (redoString) ->
    []

window.Utils = new Utils()

