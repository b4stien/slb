class Utils
  getFileJSON: (fileURL) ->
    xhr = new XMLHttpRequest()
    xhr.open 'GET', fileURL, false
    xhr.send(null)
    JSON.parse(xhr.responseText)

Utils = new Utils()
