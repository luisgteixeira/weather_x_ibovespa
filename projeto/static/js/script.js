$(function() {
    $('input[type=file]').change(function(){
      var t = $(this).val();
      var labelText = 'Arquivo: ' + t.substr(12, t.length);
      $(this).prev('label').text(labelText);
    })
  });