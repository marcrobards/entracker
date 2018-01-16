<?php

error_reporting(E_ALL);
ini_set('display_errors', True);

$year = $_GET["year"];
$path = $_GET["path"];
$team = $_GET["team"];

// DEV
$url = "http://localhost:3257";
// PROD
// TODO: set url of node server
//$url = "http://api.marcrobards.com/";

$race_url = $url."/race/".$year."/".$path."/".$team;
$race_json = file_get_contents($race_url);
//echo "json:" . $race_json;
$race = json_decode($race_json);
//echo "race_id" . $race->race_id;

date_default_timezone_set('UTC');

$time = strtotime($race->date);

$fixed = date('l, F jS Y \at g:ia', $time); 
//$year = date('Y', $time);


if (!$race->has_splits){
    // no splits, show list of members
    $table = showMembersList($race);
}
else {
    $splits_url = $url."/splits/".$year."/".$path."/".$team;
 //   echo "splits_url:" . $splits_url;
    $splits_json = file_get_contents($splits_url);
  //  echo "splits_json:" . $splits_json;
    $race = json_decode($splits_json);
    //echo "race_id:" . $race->race_id;

    $table = showSplits($race);
}

function showMembersList($race){
    if (count($race->members) == 0){
        $table = '<div class="text"><b>No known '.$race->teamName.' members racing yet.</b></div><br>';
    }
    else {
        $table = '<div class="text"><b>'. count($race->members) .' known '.$race->teamName.' members racing:</b>';
        $table .= '<table border="1"><thead><tr><th>Bib</th><th>Name</th></tr></thead><tbody>';
        foreach ($race->members as $member){
            $table .= '<tr><td>' . $member->bib . '</td><td>' . $member->name. '</td></tr>';            
        }
        $table .= '</tbody></table></div><br>';       
    }
    return $table;
}

function trimZeros($time) {
    $regex = '/^(0+:*)+/';
    $result = preg_replace($regex, '', $time);
    return $result;
}

function showSplits($race) {
    global $year, $path;
//    echo "race:" . $race->race_id;
    $race_id = $race->race_id;
    $newathlete_race_id = $race->newathlete_race_id;
    $sportstats_race_id = $race->sportstats_race_id;
    $scraper_type = $race->scraper_type;

    $table = '<table width="100%" border="1" id="splitsTable" class="tablesorter">';

    $header = '<thead><tr><th>Bib</th><th>Name</th><th>Division</th>';

    $prevType = '';
    foreach ($race->splits as $split){              
        if ($prevType == "swim" && $split->type == "bike"){
            $header .= '<th>Swim Div</th><th>T1</th>';
        }
        if ($prevType == "bike" && $split->type == "run"){
            $header .= '<th>Bike Div</th><th>T2</th>';  
        }
        $name = ucfirst($split->name);       
        if ($name == 'Total'){          
            $name = 'Total ' . ucfirst($split->type);
        }
        $name .= '<br/>(' . $split->distance . ')';
        $header .= '<th>' . $name . '</th>';
        $prevType = $split->type;
    }
    $header .= '<th>Run Div</th><th>Overall</th><th>Rank</th><th>Overall Pos.</th></tr></thead>';

    $table .= $header;

    $table .= '<tbody>';    

    foreach ($race->athletes as $bib){
        $row = '';
        if ($scraper_type == 1){
            $url = 'http://tracker.ironman.com/sportstatsv2/ironman/index.xhtml?raceid='.$sportstats_race_id.'&bib='.$bib->bib;
        }
        else if ($scraper_type == 0){
            // $url = 'http://track.ironman.com/newathlete.php?rid='.$newathlete_race_id.'&bib='.$bib->bib;
            $url = 'http://www.ironman.com/triathlon/coverage/athlete-tracker.aspx?race='.$path.'&y='.$year.'&bib='.$bib->bib;
        }
        
        $row .= '<tr><td><a href="'.$url.'" target="_blank">' . $bib->bib . '</a></td>';
        //$row .= '<tr><td>' . $bib->bib . '</td>';
        $row .= '<td id="'. $bib->bib . '_name">' . $bib->name . '</td>';
        $row .= '<td id="'. $bib->bib . '_division">' . $bib->division . '</td>';

        $prevType = '';
        $prevDivRank = '';
        foreach ($bib->splits as $split){                           
            $t1Time = '&#160';
            if (array_key_exists('t1Time', $bib)){
                $t1Time = trimZeros($bib->t1Time);
            }
            if ($prevType == "swim" && $split->type == "bike"){
                $row .= '<td id="'. $bib->bib . '_' . $prevType .'-rank">'. $prevDivRank .'</td><td id="'. $bib->bib . '_t1">'. $t1Time .'</td>';
            }
            $t2Time = '&#160';
            if (array_key_exists('t2Time', $bib)){
                $t2Time = trimZeros($bib->t2Time);
            }
            if ($prevType == "bike" && $split->type == "run"){
                $row .= '<td id="'. $bib->bib . '_' . $prevType .'-rank">'. $prevDivRank .'</td><td id="'. $bib->bib . '_t2">'. $t2Time .'</td>';
            }   
            if (array_key_exists('splitTime', $split)){
                // swim fix
                if ($split->splitTime == '--:--' && $split->type == 'swim')
                {
                    $row .= '<td id="'. $bib->bib . '_' . $split->sequence .'">'. trimZeros($split->raceTime);
                }                
                else {
                    $row .= '<td id="'. $bib->bib . '_' . $split->sequence .'">'. trimZeros($split->splitTime);
                    if (array_key_exists('pace', $split)){
                        $row .= '<br />('. $split->pace .')';           
                    }     
                }      
                $row .= '</td>';
            }           
            else{
                $row .= '<td>&#160;</td>';
            }
            
            $prevType = $split->type;
            if (array_key_exists('divisionRank', $split)){
                $prevDivRank = $split->divisionRank;
            }
            else{
                $prevDivRank = '';
            }
        }
        $overallTime = '&#160;';
        if (array_key_exists('overallTime', $bib)){
            $overallTime = trimZeros($bib->overallTime);
        }

        $divisionRank = '&#160;';
        if (array_key_exists('divisionRank', $bib)){
            $divisionRank = $bib->divisionRank;
        }

        $overallRank = '&#160;';
        if (array_key_exists('overallRank', $bib)){
            $overallRank = $bib->overallRank;
        }

        $row .= '<td id="'. $bib->bib . '_' . $split->type .'-rank">'.$prevDivRank.'</td><td id="'. $bib->bib . '_overall-time">'.$overallTime.'</td><td id="'. $bib->bib . '_division-rank">'.$divisionRank.'</td><td id="'. $bib->bib . '_overall-rank">'.$overallRank.'</td>';

        $row .= '</tr>';
        $table .= $row;
    }
    
    $table .= '</tbody></table>';

    return $table;
}

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title><?php echo $race->name ?> Tracker</title>
    <link href="/entracker/styles/tablesorter.css" rel="stylesheet" type="text/css" />
    <link href="/entracker/styles/tracker.css" rel="stylesheet" type="text/css" />
    <script src="http://cdnjs.cloudflare.com/ajax/libs/moment.js/2.5.1/moment.min.js"></script>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>	
    <script src="/entracker/scripts/jquery.tablesorter.min.js" type="text/javascript"></script>
	<script src="/entracker/scripts/static.js" type="text/javascript"></script>
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-33049301-1', 'auto');
  ga('send', 'pageview');

</script>
</head>
<body <?php if ($race->offset)  echo 'onload="startTime();beginrefresh()"'  ?>>
<a href="http://www.endurancenation.us/" target="_blank"><img src="/entracker/img/EN.Web2_.0_FullLogo_shadow-e1322948447422.png" style="float:left; margin-right: 5px;" /></a>
<br />
<div>
<span style="line-height:21.111112594604492px;color:rgb(85,85,85);font-size:14.44444465637207px;font-family:'Droid Sans','Myriad Pro',Helvetica,Arial,sans-serif">Team Endurance Nation is the world's largest, most active online triathlon team. Our more than 700 members include age group winners, course record holders, Kona qualifiers, podium finishers, front of the pack, middle of the pack, and back of the pack superstars. We are home of the First Time Finish Guarantee (<a href="http://www.endurancenation.us/firstfinish" target="_blank">www.endurancenation.us/firstfinish</a>) and creators of the Four Keys of Race Execution. We have a proven system that will get you from to race day with the support and guidance you need to be your best.  Please explore <a href="http://www.endurancenation.us/" target="_blank">our website</a> or create a <a href="https://members.endurancenation.us/Signup/SignUpOpen.aspx" target="_blank">free 7-day trial</a> to experience TeamEN for yourself!</span>
</div>
<br />
<br />
<br />
<div id="localTime" style="float:right;margin-top:25px" class="text"></div>
<h2 class="text"><?php echo $year . ' ' . $race->name ?> Tracker</h2>
<br />
<?php echo $table ?>
<?php if(!$race->is_running) echo '<!--' ?>
<div id="displaytime" class="refresh" >page auto-refresh in</div>
<a href="#" id="toggleRefresh" class="refresh">pause auto-refresh</a>
<?php if(!$race->is_running) echo '-->' ?>
<script type="text/javascript">
function startTime()
{

 		var time = moment().utc().zone(<?php echo $race->offset ?> * -1);
    var out = "Race Local Time: " + time.format("h:mm:ss A");
    $('#localTime').text(out);
    var t = setTimeout(function(){startTime()},500);

}
</script>
</body>
</html>
