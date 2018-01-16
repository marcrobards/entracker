//enter refresh time in "minutes:seconds" Minutes should range from 0 to inifinity. Seconds should range from 0 to 59
var limit = "1:00"

if (document.images) {
	var parselimit = limit.split(":")
	parselimit = parselimit[0] * 60 + parselimit[1] * 1
}

function beginrefresh() {
	if (!document.images)
		return
	if (parselimit == 1) {
		$("#displaytime").text("refreshing...");
		window.location.reload();
	}
	else {
		parselimit -= 1
		curmin = Math.floor(parselimit / 60)
		cursec = parselimit % 60
		if (curmin != 0)
			curtime = "page auto-refresh in " + curmin + " minutes and " + cursec + " seconds"
		else if (cursec == 1)
			curtime = "page auto-refresh in " + cursec + " second"
		else
			curtime = "page auto-refresh in " + cursec + " seconds"
		var value = $("#toggleRefresh").html();
		if (value == "pause auto-refresh") {
			$("#displaytime").text(curtime);
			setTimeout("beginrefresh()", 1000)
		}
	}
}


function checkTime(i)
{
	if (i<10)
	  {
	  i="0" + i;
	  }
	return i;
}
 $(document).ready(function () {
	$("#splitsTable").tablesorter();

	$("#toggleRefresh").on('click', function () {
		
		var value = $("#toggleRefresh").html();
		if (value == "pause auto-refresh") {
			$("#toggleRefresh").text("resume auto-refresh");
			$("#displaytime").text("page auto-refreshed is paused.");
		}
		else {
			$("#toggleRefresh").text("pause auto-refresh");
			$("#displaytime").text("page auto-refresh in");
			setTimeout("beginrefresh()", 1000);
		}
	});
	
	

});
