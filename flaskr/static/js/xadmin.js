;!function (win) {
	"use strict";
	var doc = document

	,Xadmin = function(){
	    this.v = '2.2'; //版本号
	}

	Xadmin.prototype.init = function() {
		var tab_list = this.get_data();
		for(var i in tab_list){
			this.add_lay_tab(tab_list[i].title,tab_list[i].url,i);
		}
		element.tabChange('xbs_tab', i);
	};
  /**
   * [end 执行结束要做的]
   * @return {[type]} [description]
   */
  Xadmin.prototype.end = function() {

    var cate_list = this.get_cate_data();

    for(var i in cate_list){
      if(cate_list[i]!=null){
        $('.left-nav #nav li').eq(cate_list[i]).click();
      }
    }
  };

	Xadmin.prototype.add_tab = function (title,url,is_refresh) {
		var id = md5(url);//md5每个url

		//重复点击
		for (var i = 0; i <$('.x-iframe').length; i++) {
            if($('.x-iframe').eq(i).attr('tab-id')==id){
                element.tabChange('xbs_tab', id);
                if(is_refresh)
                    $('.x-iframe').eq(i).attr("src",$('.x-iframe').eq(i).attr('src'));
                return;
            }
        };

		this.add_lay_tab(title,url,id);
	    this.set_data(title,url,id);
	    element.tabChange('xbs_tab', id);

	}

  Xadmin.prototype.del_tab = function (id) {

    if(id){
      console.log(88);
    }else{
      var id = $(window.frameElement).attr('tab-id');
      parent.element.tabDelete('xbs_tab', id);
    }
  }

	Xadmin.prototype.add_lay_tab = function(title,url,id) {
		element.tabAdd('xbs_tab', {
	       title: title 
	        ,content: '<iframe tab-id="'+id+'" frameborder="0" src="'+url+'" scrolling="yes" class="x-iframe"></iframe>'
	        ,id: id
	    })
	}
	/**
	 * [open 打开弹出层]
	 * @param  {[type]}  title [弹出层标题]
	 * @param  {[type]}  url   [弹出层地址]
	 * @param  {[type]}  w     [宽]
	 * @param  {[type]}  h     [高]
	 * @param  {Boolean} full  [全屏]
	 * @return {[type]}        [description]
	 */
	Xadmin.prototype.open = function (title,url,w,h,full) {
		if (title == null || title == '') {
	        var title=false;
	    };
	    if (url == null || url == '') {
	        var url="404.html";
	    };
	    if (w == null || w == '') {
	        var w=($(window).width()*0.9);
	    };
	    if (h == null || h == '') {
	        var h=($(window).height() - 50);
	    };
	    var index = layer.open({
	        type: 2,
	        area: [w+'px', h +'px'],
	        fix: false, //不固定
	        maxmin: true,
	        shadeClose: true,
	        shade:0.4,
	        title: title,
	        content: url
	    });
	    if(full){
	       layer.full(index); 
	    }
	}
	/**
	 * [close 关闭弹出层]
	 * @return {[type]} [description]
	 */
	Xadmin.prototype.close = function() {
		var index = parent.layer.getFrameIndex(window.name);
    	parent.layer.close(index);
	};
  /**
   * [close 关闭弹出层父窗口关闭]
   * @return {[type]} [description]
   */
  Xadmin.prototype.father_reload = function() {
      parent.location.reload();
  };
	/**
	 * [get_data 获取所有项]
	 * @return {[type]} [description]
	 */
	Xadmin.prototype.get_data = function () {
    if(typeof is_remember!="undefined")
          return false;
		return layui.data('tab_list')
	}
	/**
	 * [set_data 增加某一项]
	 * @param {[type]} id [description]
	 */
	Xadmin.prototype.set_data = function(title,url,id) {

		if(typeof is_remember!="undefined")
        	return false;

		layui.data('tab_list', {
		  key: id
		  ,value: {title:title,url:url}
		});
	};

  /**
   * [get_data 获取所有项]
   * @return {[type]} [description]
   */
  Xadmin.prototype.get_cate_data = function () {
    if(typeof is_remember!="undefined")
          return false;
    return layui.data('cate')
  }
  /**
   * [set_data 增加某一项]
   * @param {[type]} id [description]
   */
  Xadmin.prototype.set_cate_data = function(data) {

    if(typeof is_remember!="undefined")
          return false;

    layui.data('cate', data);
  };
	/**
	 * [del_data 删除某一项]
	 * @param  {[type]} id [description]
	 * @return {[type]}    [description]
	 */
	Xadmin.prototype.del_data = function(id) {
		if(typeof is_remember!="undefined")
        	return false;
		if(typeof id!="undefined"){
			layui.data('tab_list', {
			  key: id
			  ,remove: true
			});
		}else{
			layui.data('tab_list',null);
		}
	};
	/**
	 * [del_other_data 删除其它]
	 * @param  {[type]} id [description]
	 * @return {[type]}    [description]
	 */
	Xadmin.prototype.del_other_data = function(id) {
		if(typeof is_remember!="undefined")
        	return false;
		var tab_list = this.get_data();

		layui.data('tab_list',null);

		layui.data('tab_list', {
		  key: id
		  ,value: tab_list[id]
		});
	};
	win.xadmin = new Xadmin();
	
}(window);

layui.use(['layer','element','jquery'],function() {
    layer = layui.layer;
    element = layui.element;
    $ = layui.jquery;


    // 打开页面初始
    xadmin.init();

    //关闭tab清除记忆
    element.on('tabDelete(xbs_tab)', function(data){
        var id  = $(this).parent().attr('lay-id');
        xadmin.del_data(id);
    });
    //左侧菜单
    $('.left-nav #nav').on('click', 'li', function(event) {

        if($(this).parent().attr('id')=='nav'){
          xadmin.set_cate_data({key:'f1',value:$('.left-nav #nav li').index($(this))})
          xadmin.set_cate_data({key:'f2',value:null})
          xadmin.set_cate_data({key:'f3',value:null})
        }

        if($(this).parent().parent().parent().attr('id')=='nav'){
          xadmin.set_cate_data({key:'f2',value:$('.left-nav #nav li').index($(this))})
          xadmin.set_cate_data({key:'f3',value:null})
        }

        if($(this).parent().parent().parent().parent().parent().attr('id')=='nav'){
          xadmin.set_cate_data({key:'f3',value:$('.left-nav #nav li').index($(this))})
        }



        if($('.left-nav').css('width')=='60px'){
          $('.left-nav').animate({width: '220px'}, 100);
          $('.page-content').animate({left: '220px'}, 100);
          $('.left-nav i').css('font-size','14px');
          $('.left-nav cite,.left-nav .nav_right').show();
        }

        if($(window).width()<768){
            $('.page-content-bg').show();
        }

        $('.left-nav').find('a').removeClass('active');
        $(this).children('a').addClass('active');
        if($(this).children('.sub-menu').length){
            if($(this).hasClass('open')){
                $(this).removeClass('open');
                $(this).find('.nav_right').html('&#xe697;');
                $(this).children('.sub-menu').stop(true,true).slideUp();
                $(this).siblings().children('.sub-menu').slideUp();
            }else{
                $(this).addClass('open');
                $(this).children('a').find('.nav_right').html('&#xe6a6;');
                $(this).children('.sub-menu').stop(true,true).slideDown();
                $(this).siblings().children('.sub-menu').stop(true,true).slideUp();
                $(this).siblings().find('.nav_right').html('&#xe697;');
                $(this).siblings().removeClass('open');
            }
        }
        event.stopPropagation(); 
    })
    var left_tips_index = null;
    $('.left-nav #nav').on('mouseenter', '.left-nav-li', function(event) {
      if($('.left-nav').css('width')!='220px'){
        var tips  = $(this).attr('lay-tips');
        left_tips_index = layer.tips(tips, $(this));
      }
    })

    $('.left-nav #nav').on('mouseout', '.left-nav-li', function(event) {
        layer.close(left_tips_index); 
    })
    // 隐藏左侧
    $('.container .left_open i').click(function(event) {
        if($('.left-nav').css('width')=='220px'){
            $('.left-nav .open').click();
            $('.left-nav i').css('font-size','18px');
            $('.left-nav').animate({width: '60px'}, 100);
            $('.left-nav cite,.left-nav .nav_right').hide();
            $('.page-content').animate({left: '60px'}, 100);
            $('.page-content-bg').hide();
        }else{
            $('.left-nav').animate({width: '220px'}, 100);
            $('.page-content').animate({left: '220px'}, 100);
            $('.left-nav i').css('font-size','14px');
            $('.left-nav cite,.left-nav .nav_right').show();
            if($(window).width()<768){
                $('.page-content-bg').show();
            }
        }

    });

    $('.page-content-bg').click(function(event) {
        $('.left-nav .open').click();
        $('.left-nav i').css('font-size','18px');
        $('.left-nav').animate({width: '60px'}, 100);
        $('.left-nav cite,.left-nav .nav_right').hide();
        $('.page-content').animate({left: '60px'}, 100);
        $(this).hide();
    });

    $(".layui-tab-title").on('contextmenu', 'li', function(event) {
        var tab_left = $(this).position().left;
        var tab_width = $(this).width();
        var left = $(this).position().top;
        var this_index = $(this).attr('lay-id');
        $('#tab_right').css({'left':tab_left+tab_width/2}).show().attr('lay-id',this_index);
        $('#tab_show').show();
        return false;
    });

    $('#tab_right').on('click', 'dd', function(event) {
        var data_type = $(this).attr('data-type');
        var lay_id = $(this).parents('#tab_right').attr('lay-id');
        if(data_type=='this'){
          $('.layui-tab-title li[lay-id='+lay_id+']').find('.layui-tab-close').click();
        }else if(data_type=='other'){
          $('.layui-tab-title li').eq(0).find('.layui-tab-close').remove();
          $('.layui-tab-title li[lay-id!='+lay_id+']').find('.layui-tab-close').click();
        }else if(data_type=='all'){
          $('.layui-tab-title li[lay-id]').find('.layui-tab-close').click();
        }
        $('#tab_right').hide();
        $('#tab_show').hide();
    })


    $('.page-content,#tab_show,.container,.left-nav').click(function(event) {
        $('#tab_right').hide();
        $('#tab_show').hide();
    });

    // 页面加载完要做的
    xadmin.end();
})
// md5-----------------------------------------------------------------------------------
/*
* Add integers, wrapping at 2^32. This uses 16-bit operations internally
* to work around bugs in some JS interpreters.
*/
function safeAdd (x, y) {
var lsw = (x & 0xffff) + (y & 0xffff)
var msw = (x >> 16) + (y >> 16) + (lsw >> 16)
return (msw << 16) | (lsw & 0xffff)
}

/*
* Bitwise rotate a 32-bit number to the left.
*/
function bitRotateLeft (num, cnt) {
return (num << cnt) | (num >>> (32 - cnt))
}

/*
* These functions implement the four basic operations the algorithm uses.
*/
function md5cmn (q, a, b, x, s, t) {
return safeAdd(bitRotateLeft(safeAdd(safeAdd(a, q), safeAdd(x, t)), s), b)
}
function md5ff (a, b, c, d, x, s, t) {
return md5cmn((b & c) | (~b & d), a, b, x, s, t)
}
function md5gg (a, b, c, d, x, s, t) {
return md5cmn((b & d) | (c & ~d), a, b, x, s, t)
}
function md5hh (a, b, c, d, x, s, t) {
return md5cmn(b ^ c ^ d, a, b, x, s, t)
}
function md5ii (a, b, c, d, x, s, t) {
return md5cmn(c ^ (b | ~d), a, b, x, s, t)
}

/*
* Calculate the MD5 of an array of little-endian words, and a bit length.
*/
function binlMD5 (x, len) {
/* append padding */
x[len >> 5] |= 0x80 << (len % 32)
x[((len + 64) >>> 9 << 4) + 14] = len

var i
var olda
var oldb
var oldc
var oldd
var a = 1732584193
var b = -271733879
var c = -1732584194
var d = 271733878

for (i = 0; i < x.length; i += 16) {
  olda = a
  oldb = b
  oldc = c
  oldd = d

  a = md5ff(a, b, c, d, x[i], 7, -680876936)
  d = md5ff(d, a, b, c, x[i + 1], 12, -389564586)
  c = md5ff(c, d, a, b, x[i + 2], 17, 606105819)
  b = md5ff(b, c, d, a, x[i + 3], 22, -1044525330)
  a = md5ff(a, b, c, d, x[i + 4], 7, -176418897)
  d = md5ff(d, a, b, c, x[i + 5], 12, 1200080426)
  c = md5ff(c, d, a, b, x[i + 6], 17, -1473231341)
  b = md5ff(b, c, d, a, x[i + 7], 22, -45705983)
  a = md5ff(a, b, c, d, x[i + 8], 7, 1770035416)
  d = md5ff(d, a, b, c, x[i + 9], 12, -1958414417)
  c = md5ff(c, d, a, b, x[i + 10], 17, -42063)
  b = md5ff(b, c, d, a, x[i + 11], 22, -1990404162)
  a = md5ff(a, b, c, d, x[i + 12], 7, 1804603682)
  d = md5ff(d, a, b, c, x[i + 13], 12, -40341101)
  c = md5ff(c, d, a, b, x[i + 14], 17, -1502002290)
  b = md5ff(b, c, d, a, x[i + 15], 22, 1236535329)

  a = md5gg(a, b, c, d, x[i + 1], 5, -165796510)
  d = md5gg(d, a, b, c, x[i + 6], 9, -1069501632)
  c = md5gg(c, d, a, b, x[i + 11], 14, 643717713)
  b = md5gg(b, c, d, a, x[i], 20, -373897302)
  a = md5gg(a, b, c, d, x[i + 5], 5, -701558691)
  d = md5gg(d, a, b, c, x[i + 10], 9, 38016083)
  c = md5gg(c, d, a, b, x[i + 15], 14, -660478335)
  b = md5gg(b, c, d, a, x[i + 4], 20, -405537848)
  a = md5gg(a, b, c, d, x[i + 9], 5, 568446438)
  d = md5gg(d, a, b, c, x[i + 14], 9, -1019803690)
  c = md5gg(c, d, a, b, x[i + 3], 14, -187363961)
  b = md5gg(b, c, d, a, x[i + 8], 20, 1163531501)
  a = md5gg(a, b, c, d, x[i + 13], 5, -1444681467)
  d = md5gg(d, a, b, c, x[i + 2], 9, -51403784)
  c = md5gg(c, d, a, b, x[i + 7], 14, 1735328473)
  b = md5gg(b, c, d, a, x[i + 12], 20, -1926607734)

  a = md5hh(a, b, c, d, x[i + 5], 4, -378558)
  d = md5hh(d, a, b, c, x[i + 8], 11, -2022574463)
  c = md5hh(c, d, a, b, x[i + 11], 16, 1839030562)
  b = md5hh(b, c, d, a, x[i + 14], 23, -35309556)
  a = md5hh(a, b, c, d, x[i + 1], 4, -1530992060)
  d = md5hh(d, a, b, c, x[i + 4], 11, 1272893353)
  c = md5hh(c, d, a, b, x[i + 7], 16, -155497632)
  b = md5hh(b, c, d, a, x[i + 10], 23, -1094730640)
  a = md5hh(a, b, c, d, x[i + 13], 4, 681279174)
  d = md5hh(d, a, b, c, x[i], 11, -358537222)
  c = md5hh(c, d, a, b, x[i + 3], 16, -722521979)
  b = md5hh(b, c, d, a, x[i + 6], 23, 76029189)
  a = md5hh(a, b, c, d, x[i + 9], 4, -640364487)
  d = md5hh(d, a, b, c, x[i + 12], 11, -421815835)
  c = md5hh(c, d, a, b, x[i + 15], 16, 530742520)
  b = md5hh(b, c, d, a, x[i + 2], 23, -995338651)

  a = md5ii(a, b, c, d, x[i], 6, -198630844)
  d = md5ii(d, a, b, c, x[i + 7], 10, 1126891415)
  c = md5ii(c, d, a, b, x[i + 14], 15, -1416354905)
  b = md5ii(b, c, d, a, x[i + 5], 21, -57434055)
  a = md5ii(a, b, c, d, x[i + 12], 6, 1700485571)
  d = md5ii(d, a, b, c, x[i + 3], 10, -1894986606)
  c = md5ii(c, d, a, b, x[i + 10], 15, -1051523)
  b = md5ii(b, c, d, a, x[i + 1], 21, -2054922799)
  a = md5ii(a, b, c, d, x[i + 8], 6, 1873313359)
  d = md5ii(d, a, b, c, x[i + 15], 10, -30611744)
  c = md5ii(c, d, a, b, x[i + 6], 15, -1560198380)
  b = md5ii(b, c, d, a, x[i + 13], 21, 1309151649)
  a = md5ii(a, b, c, d, x[i + 4], 6, -145523070)
  d = md5ii(d, a, b, c, x[i + 11], 10, -1120210379)
  c = md5ii(c, d, a, b, x[i + 2], 15, 718787259)
  b = md5ii(b, c, d, a, x[i + 9], 21, -343485551)

  a = safeAdd(a, olda)
  b = safeAdd(b, oldb)
  c = safeAdd(c, oldc)
  d = safeAdd(d, oldd)
}
return [a, b, c, d]
}

/*
* Convert an array of little-endian words to a string
*/
function binl2rstr (input) {
var i
var output = ''
var length32 = input.length * 32
for (i = 0; i < length32; i += 8) {
  output += String.fromCharCode((input[i >> 5] >>> (i % 32)) & 0xff)
}
return output
}

/*
* Convert a raw string to an array of little-endian words
* Characters >255 have their high-byte silently ignored.
*/
function rstr2binl (input) {
var i
var output = []
output[(input.length >> 2) - 1] = undefined
for (i = 0; i < output.length; i += 1) {
  output[i] = 0
}
var length8 = input.length * 8
for (i = 0; i < length8; i += 8) {
  output[i >> 5] |= (input.charCodeAt(i / 8) & 0xff) << (i % 32)
}
return output
}

/*
* Calculate the MD5 of a raw string
*/
function rstrMD5 (s) {
return binl2rstr(binlMD5(rstr2binl(s), s.length * 8))
}

/*
* Calculate the HMAC-MD5, of a key and some data (raw strings)
*/
function rstrHMACMD5 (key, data) {
var i
var bkey = rstr2binl(key)
var ipad = []
var opad = []
var hash
ipad[15] = opad[15] = undefined
if (bkey.length > 16) {
  bkey = binlMD5(bkey, key.length * 8)
}
for (i = 0; i < 16; i += 1) {
  ipad[i] = bkey[i] ^ 0x36363636
  opad[i] = bkey[i] ^ 0x5c5c5c5c
}
hash = binlMD5(ipad.concat(rstr2binl(data)), 512 + data.length * 8)
return binl2rstr(binlMD5(opad.concat(hash), 512 + 128))
}

/*
* Convert a raw string to a hex string
*/
function rstr2hex (input) {
var hexTab = '0123456789abcdef'
var output = ''
var x
var i
for (i = 0; i < input.length; i += 1) {
  x = input.charCodeAt(i)
  output += hexTab.charAt((x >>> 4) & 0x0f) + hexTab.charAt(x & 0x0f)
}
return output
}

/*
* Encode a string as utf-8
*/
function str2rstrUTF8 (input) {
return unescape(encodeURIComponent(input))
}

/*
* Take string arguments and return either raw or hex encoded strings
*/
function rawMD5 (s) {
return rstrMD5(str2rstrUTF8(s))
}
function hexMD5 (s) {
return rstr2hex(rawMD5(s))
}
function rawHMACMD5 (k, d) {
return rstrHMACMD5(str2rstrUTF8(k), str2rstrUTF8(d))
}
function hexHMACMD5 (k, d) {
return rstr2hex(rawHMACMD5(k, d))
}

function md5 (string, key, raw) {
if (!key) {
  if (!raw) {
    return hexMD5(string)
  }
  return rawMD5(string)
}
if (!raw) {
  return hexHMACMD5(key, string)
}
return rawHMACMD5(key, string)
}