$(document).ready(function() {
   var navFlag = true;
   var navbar = $('div#nav');
   var wrapper = $('div#content-wrapper');
   console.log(1);
   $('#nav-hide').click(function() {
      var self = $(this);
      console.log('2');
      //navbar.toggleClass('nav-active');
      //wrapper.toggleClass('nav-active');
      if(navFlag) {
         wrapper.animate({'margin-left':'100px'},200);
         navbar.animate({'left':'0'},200);
      } else {
         wrapper.animate({'margin-left':'0'},200);
         navbar.animate({'left':'-100px'},200);
      }
      navFlag = !navFlag;
      self.toggleClass('nav-active');
   });

   if(checkIpod()) {
      $('li.menu').click(function() {
         self = $(this).children('ul.submenu');
         self.toggleClass('self');
         state = self.hasClass('on')
         navAnim(self,state);
         var subs = $('ul.submenu');
         for(i = 0; i < subs.length; i++) {
            x = $(subs[i]);
            if(x.hasClass('on') && !x.hasClass('self')) navAnim(x,true);
         }
         self.toggleClass('self');
      });
   }
});

var navAnim = function(self, state) {
   if(state) {
      self.css('overflow','hidden');
      self.animate({width:'0px'}, 'fast');
      console.log(1);
   } else {
      //self.css('overflow','visible');
      self.css('overflow','visible');
      self.animate({width:'120px'}, 'fast');
      console.log(2);
   }
   self.toggleClass('on');
}

var checkIpod = function() {
   return (
      (navigator.platform.indexOf("iPad") != -1) ||
      (navigator.platform.indexOf("iPod") != -1) ||
      (navigator.platform.indexOf("iPhone") != -1)
   )

}
