$(document).ready(function() {
   var a = $('#text')
   a.attr('contenteditable', true)
   a.ckeditor()

   $('button[value=submit]').on('click', function(e) {
      console.log($('input[name=text]').attr('value',$('div#text').html()))
   });
});
