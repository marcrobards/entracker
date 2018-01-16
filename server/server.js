var express = require('express');

var EasyMySQL = require('easy-mysql');

var mysql = require('mysql');

var app = express();
var server = require('http').createServer(app);

var port = 3257;

// TODO: set db settings
var settings = {    
    host     : 'XXX.XXX.XX.XXX',
    user     : 'marc',
    password : 'XXXXX',
    database : 'triathlete_tracker'
  };

var easy_mysql = EasyMySQL.connect(settings);

// Add headers
app.use(function (req, res, next) {

  // Website you wish to allow to connect 
  // DEV
  res.setHeader('Access-Control-Allow-Origin', '*');
  // PROD
  // TODO: set url of website
  // res.setHeader('Access-Control-Allow-Origin', 'http://[url of website]');

  // Request methods you wish to allow
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');

  // Request headers you wish to allow
  res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');

  // Set to true if you need the website to include cookies in the requests sent
  // to the API (e.g. in case you use sessions)
  res.setHeader('Access-Control-Allow-Credentials', true);

  // Pass to next layer of middleware
  next();
});

app.get("/", function(req, res){
  var response = {"message": "Hello from the EN Tracker API"};
  res.jsonp(response);
});

app.get("/team/:path", function(req, res){
  var team_path = req.params["path"];
  
  getTeam(team_path, res);
});

app.get("/race/:year/:path/:team", function(req, res) {
  var year = req.params["year"];
  var path = req.params["path"];
  var team = req.params["team"];

  getRace(year, path, team, res);
});

app.get("/splits/:year/:path/:team", function(req, res){
  var year = req.params["year"];
  var path = req.params["path"];
  var team = req.params["team"];
  
  getSplits(year, path, team, res);    
});

server.listen(port);
console.log("Listening on port ", port);

function getTeam(team_path, res){
  console.log('in getTeam');
  var team_sql = "SELECT * \
  FROM teams t \
  WHERE t.path = ?;"
  easy_mysql.get_one(team_sql, [team_path], function(err, result){
    if (err) {      
      var msg = "Error!" + err
      console.log(msg);
      var errobj = {};
      errobj.error = msg;
      res.jsonp(errobj);
    }
    else {
      res.jsonp(result);
    }
  });
}

function getSplits(year, path, team, res){
  var race = {};
  var prev_bib = 0;
  var prev_sequence = 0;

  var splits_sql = "SELECT \
  r.name, \
  r.race_id, \
  r.newathlete_race_id, \
  r.sportstats_race_id, \
  r.scraper_type, \
  r.name as race_name, \
  r.is_running, \
  r.race_date, \
  r.timezone_offset, \
  a.athlete_id, \
  a.name as athlete_name, \
  a.bib, \
  a.division, \
  a.residence, \
  a.country, \
  a.occupation, \
  a.division_rank, \
  a.division_total, \
  a.overall_rank, \
  a.overall_total, \
  a.gender_rank, \
  a.gender_total, \
  a.swim_time, \
  a.t1_time, \
  a.bike_time, \
  a.t2_time, \
  a.run_time, \
  a.overall_time, \
  s.sequence, \
  s.`type`, \
  s.name as split_name, \
  s.distance as split_distance, \
  s.split_time, \
  s.race_time, \
  s.pace, \
  s.division_rank as split_division_rank, \
  s.overall_rank as split_overall_rank, \
  s.gender_rank as split_gender_rank, \
  a.last_updated \
  FROM races r \
  LEFT JOIN athletes a ON r.race_id = a.race_id \
  LEFT JOIN splits s ON a.athlete_id = s.athlete_id AND r.race_id = s.race_id \
  LEFT JOIN teams_members m on a.member_id = m.member_id \
  LEFT JOIN teams t on m.team_id = t.team_id  \
  WHERE r.year = ? \
  AND r.path = ? \
  AND t.path = ? \
  ORDER BY a.bib, s.sequence;";

  easy_mysql.get_all(splits_sql, [year, path, team], function(err, result) {
    if (err || !result) {
      var msg = "Error!" + err
      console.log(msg);
      var errobj = {};
      errobj.error = msg;
      res.jsonp(errobj);
    } else {
      result.forEach(function(split){
        if (Object.keys(race).length === 0){
          race = {
            "race_id": split.race_id,
            "newathlete_race_id": split.newathlete_race_id,
            "sportstats_race_id": split.sportstats_race_id,
            "scraper_type": split.scraper_type,
            "is_running": split.is_running,            
            "name": split.race_name,
            "date": split.race_date,
            "offset": split.timezone_offset,
            "splits": [],
            "athletes": [],
          }
        }
        var athlete = {};
        if (split.bib !== prev_bib){
                    //athlete.athlete_id = split.athlete_id;
                    if (split.athlete_name) athlete.name = split.athlete_name;
                    if (split.bib) athlete.bib = split.bib;
                    if (split.division) athlete.division = split.division;
                    if (split.residence) athlete.residence = split.residence;
                    if (split.country) athlete.country = split.country;
                    if (split.occupation) athlete.occupation = split.occupation;
                    if (split.division_rank) athlete.divisionRank = split.division_rank;
                    if (split.division_total) athlete.divisionTotal = split.division_total;
                    if (split.overall_rank) athlete.overallRank = split.overall_rank;
                    if (split.overall_total) athlete.overallTotal = split.overall_total;
                    if (split.gender_rank) athlete.genderRank = split.gender_rank;
                    if (split.gender_total) athlete.genderTotal = split.gender_total;
                    if (split.swim_time) athlete.swimTime = split.swim_time;
                    if (split.t1_time) athlete.t1Time = split.t1_time;
                    if (split.bike_time) athlete.bikeTime = split.bike_time;
                    if (split.t2_time) athlete.t2Time = split.t2_time;
                    if (split.run_time) athlete.runTime = split.run_time;
                    if (split.overall_time) athlete.overallTime = split.overall_time;
                    athlete.lastUpdated = split.last_updated;
                    athlete.splits = [];
                    prev_bib = athlete.bib;
                    if (athlete.bib){
                      race.athletes.push(athlete);
                    }
                    if (race.splits.length > 0){
                      race.has_splits = true;
                    }
                  }
                  else {
                    athlete = race.athletes[race.athletes.length-1];
                  }
                  if (!race.has_splits){
                    if (split.sequence) {
                      var race_split = {
                        "sequence": split.sequence,
                        "type": split.type,
                        "name": split.split_name,
                        "distance": split.split_distance
                      };
                      race.splits.push(race_split);
                    }
                  }
                  var new_split = {};
                  if (split.sequence) new_split.sequence = split.sequence;
                  if (split.type) new_split.type = split.type;
                  if (split.split_time) new_split.splitTime = split.split_time;
                  if (split.race_time) new_split.raceTime = split.race_time;
                  if (split.pace) new_split.pace = split.pace;
                  if (split.split_division_rank) new_split.divisionRank = split.split_division_rank;
                  if (split.split_overall_rank) new_split.overallRank = split.split_overall_rank;
                  if (split.split_gender_rank) new_split.genderRank = split.split_gender_rank;
                  athlete.splits.push(new_split);
                });
  res.jsonp(race);  
    }
  });
}

function getRace(year, path, team, res){
  var race_sql = "SELECT \
  r.name, \
  r.race_id, \
  r.newathlete_race_id, \
  r.sportstats_race_id, \
  r.name as race_name, \
  r.is_running, \
  r.race_date, \
  r.timezone_offset \
  FROM races r \
  WHERE r.year = ? AND r.path = ?";
  easy_mysql.get_one(race_sql, [year, path], function(err, race_result) {
    if (err || !race_result) {
      var msg = "Error!" + err
      console.log(msg);
      var errobj = {};
      errobj.error = msg;
      res.jsonp(errobj);
    }
    else {
      var team_sql = "SELECT t.short_name FROM teams t WHERE t.path = ?";
      easy_mysql.get_one(team_sql, [team], function(err, team_result) {
        if (err || !team_result) {
          var msg = "Error!" + err
          console.log(msg);
          var errobj = {};
          errobj.error = msg;
          res.jsonp(errobj);
        }
        else {
          race = {
            "race_id": race_result.race_id,
            "newathlete_race_id": race_result.newathlete_race_id,
            "sportstats_race_id": race_result.sportstats_race_id,
            "name": race_result.race_name,
            "is_running": race_result.is_running,
            "date": race_result.race_date,
            "offset": race_result.timezone_offset,
            "has_splits": false
          }
          race.teamName = team_result.short_name;
          var members = [];
          var members_sql = "SELECT \
          a.athlete_id, \
          a.bib, \
          m.display_name \
          FROM athletes a \
          INNER JOIN races r ON a.race_id = r.race_id \
          INNER JOIN members m ON a.member_id = m.member_id \
          INNER JOIN teams_members tm ON m.member_id = tm.member_id \
          INNER JOIN teams t ON tm.team_id = t.team_id \
          WHERE r.year = ? AND r.path = ? AND t.path = ? \
          ORDER BY m.last_name, m.first_name";
          easy_mysql.get_all(members_sql, [year, path, team], function(err, mem_results) {
            if (err || !mem_results) {
              var msg = "Error!" + err
              console.log(msg);
              var errobj = {};
              errobj.error = msg;
              res.jsonp(errobj);
            }
            else {
              member_ids = [];
              mem_results.forEach(function(m){
                member_ids.push(m.athlete_id);
                member = {
                  "bib": m.bib,
                  "name": m.display_name
                };
                members.push(member);
              });
              race.members = members;
              // check for splits
              if (member_ids.length > 0) {
                var splits_sql = "SELECT \
                count(*) as splits \
                FROM splits s \
                WHERE s.race_id = ? and s.athlete_id in (?);";
                var splits_format = mysql.format(splits_sql, [race_result.race_id, member_ids]);
                // console.log(splits_format);
                easy_mysql.get_one(splits_format, function(err, split_results) {
                  if (err) {
                    var msg = "Error!" + err
                    console.log(msg);
                    var errobj = {};
                    errobj.error = msg;
                    res.jsonp(errobj);
                  }
                  else if (!split_results || split_results.length == 0) {
                    console.log("no splits");
                  }
                  else {
                    console.log(split_results);
                    if (split_results.splits > 0) {
                      console.log("has splits");
                      race.has_splits = true;
                    }
                    res.jsonp(race);
                  }
                });
              }
              else {
                res.jsonp(race);
              }
            }
          });
        }
      });
    }
  });
}