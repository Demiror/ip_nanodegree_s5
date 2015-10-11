$(function(){
  $('.header').click(function(){
    $(this).closest('.container').toggleClass('collapsed');
  });
});