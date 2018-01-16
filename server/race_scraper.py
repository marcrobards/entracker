__author__ = 'Marc'

import urllib2
from bs4 import BeautifulSoup
import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from logging import handlers


class Athlete:
    def __init__(self):
        self.bib = None
        self.name = None
        self.division = None
        self.residence = None
        self.country = None
        self.occupation = None
        self.division_rank = None
        self.division_total = None
        self.gender_rank = None
        self.gender_total = None
        self.overall_rank = None
        self.overall_total = None
        self.swim_time = None
        self.t1_time = None
        self.bike_time = None
        self.t2_time = None
        self.run_time = None
        self.overall_time = None
        self.splits = []
        self.split_seq = 0

    def add_split(self, split):
        self.split_seq += 1
        split.sequence = self.split_seq
        self.splits.append(split)


class Split:
    def __init__(self):
        self.split_id = None
        self.sequence = None
        self.name = None
        self.type = None
        self.distance = None
        self.split_time = None
        self.race_time = None
        self.pace = None
        self.division_rank = None
        self.overall_rank = None
        self.gender_rank = None
        self.time_of_day = None


class NewAthleteScraper:
    def __init__(self, env):
        self.url_template = "http://tracking.ironmanlive.com/newathlete.php?rid={race_id}&bib={bib}"
        self.race_id_column = "newathlete_race_id"

    def close(self):
        # clean up anything
        return

    def scrape_athlete(self, url, bib, athlete_name):
        page = urllib2.urlopen(url).read()
        soup = BeautifulSoup(page)
        athlete = Athlete()
        self.scrape_athlete_info(soup, athlete)
        self.scrape_athlete_total_times(soup, athlete)
        self.scrape_athlete_splits(soup, athlete)
        return athlete

    def scrape_athlete_info(self, soup, athlete):
        # athlete.name = soup.h2.string.replace("'", "''")
        athlete.name = soup.h1.text.replace("'", "''")
        division_rank = soup.find(id="rank")
        division_ranks = division_rank.contents[1].strip().split()
        athlete_division_rank = division_ranks[0]
        if not (athlete_division_rank == "--" or athlete_division_rank == '0' or athlete_division_rank == 'DNF'):
            athlete.division_rank = int(athlete_division_rank)
        if len(division_ranks) > 1:
            athlete.division_total = int(division_ranks[2])
        overall_rank = soup.find(id="div-rank")
        overall_ranks = overall_rank.contents[1].strip().split()
        athlete_overall_rank = overall_ranks[0]
        if not (athlete_overall_rank == "--" or athlete_overall_rank == '0' or athlete_overall_rank == 'DNF'):
            athlete.overall_rank = int(athlete_overall_rank)
        if len(overall_ranks) > 1:
            athlete.overall_total = int(overall_ranks[2])
        info_table = soup.find(id="general-info")

        contents_start = 3
        contents_index = 1
        contents_value = 3

        # athlete.bib = info_table.contents[contents_start].contents[self.contents_val].text.strip()
        athlete.bib = info_table.contents[contents_start].contents[contents_index].contents[contents_value].text.strip()
        contents_index += 2
        athlete.division = info_table.contents[contents_start].contents[contents_index].contents[
            contents_value].text.strip()
        contents_index += 2
        athlete.residence = info_table.contents[contents_start].contents[contents_index].contents[
            contents_value].text.strip()
        contents_index += 2
        athlete.country = info_table.contents[contents_start].contents[contents_index].contents[
            contents_value].text.strip()
        contents_index += 2
        athlete.occupation = info_table.contents[contents_start].contents[contents_index].contents[
            contents_value].text.strip()

    def scrape_athlete_total_times(self, soup, athlete):
        contents_value = 3

        swim_time_tag = soup.find(text="Swim:")
        if swim_time_tag:
            swim_time_tag = swim_time_tag.parent.parent.parent
            athlete_swim_time = swim_time_tag.contents[contents_value].text
            if not athlete_swim_time == "--:--":
                athlete.swim_time = athlete_swim_time

        bike_time_tag = soup.find(text="Bike")
        if bike_time_tag:
            bike_time_tag = bike_time_tag.parent.parent.parent
            athlete_bike_time = bike_time_tag.contents[contents_value].text
            if not athlete_bike_time == "--:--":
                athlete.bike_time = athlete_bike_time

        run_time_tag = soup.find(text="Run")
        if run_time_tag:
            run_time_tag = run_time_tag.parent.parent.parent
            athlete_run_time = run_time_tag.contents[contents_value].text
            if not athlete_run_time == "--:--":
                athlete.run_time = athlete_run_time

        overall_time_tag = soup.find(text="Overall")
        if overall_time_tag:
            overall_time_tag = overall_time_tag.parent.parent.parent
            athlete_overall_time = overall_time_tag.contents[contents_value].text
            if not athlete_overall_time == "--:--":
                athlete.overall_time = athlete_overall_time

        t1_tag = soup.find(text="T1:  Swim-to-bike")
        if t1_tag:
            t1_tag = t1_tag.parent.parent
            athlete_t1_time = t1_tag.contents[contents_value].text
            if not athlete_t1_time == "--:--":
                athlete.t1_time = athlete_t1_time

        t2_tag = soup.find(text="T2: Bike-to-run")
        if t2_tag:
            t2_tag = t2_tag.parent.parent
            athlete_t2_time = t2_tag.contents[contents_value].text
            if not athlete_t2_time == "--:--":
                athlete.t2_time = athlete_t2_time

    def scrape_athlete_splits(self, soup, athlete):
        self.scrape_segment(soup, athlete, "swim", 0)
        self.scrape_segment(soup, athlete, "bike", 1)
        self.scrape_segment(soup, athlete, "run", 1)

    def scrape_segment(self, soup, athlete, seg_type, space):
        if space:
            seg_text = seg_type.title() + " Details "
        else:
            seg_text = seg_type.title() + " Details"
        soup_text = soup.find(text=seg_text.upper())
        if soup_text:
            table = soup_text.parent.parent.next_sibling.next_sibling
            tbody = table.tbody
            if tbody:
                trs = tbody.find_all('tr')
                for tr in trs:
                    split = self.scrape_split(soup, tr)
                    split.type = seg_type
                    athlete.add_split(split)
            else:
                trs = table.find_all('tr')
                for tr in trs:
                    if tr.find_all('td'):
                        split = self.scrape_split(soup, tr)
                        split.type = seg_type
                        athlete.add_split(split)
            # scrape total
            # tfoot = table.tfoot
            tfoot = soup.find_all('tfoot')
            if tfoot:
                tr = None
                if seg_type == "swim":
                    tr = tfoot[0].tr
                if seg_type == "bike":
                    if len(tfoot) == 3:
                        tr = tfoot[1].tr
                    else:
                        tr = tfoot[0].tr
                if seg_type == "run":
                    if len(tfoot) == 3:
                        tr = tfoot[2].tr
                    else:
                        tr = tfoot[1].tr
                if tr:
                    split = self.scrape_split(soup, tr)
                    split.type = seg_type
                    athlete.add_split(split)

    def scrape_split(self, soup, tr):
        # print tr
        split = Split()
        tds = tr.find_all('td')
        if tds[0].text:
            split.name = tds[0].text
        if tds[1].text:
            split.distance = tds[1].text
        if tds[2].text:
            split.split_time = tds[2].text
        if tds[3].text:
            split.race_time = tds[3].text
        if tds[4].text:
            split.pace = tds[4].text
        if not (tds[5].text == "--:--" or tds[5].text == "" or tds[5].text == "--"):
            split.division_rank = int(tds[5].text)
        if not (tds[6].text == "--:--" or tds[6].text == "" or tds[6].text == "--"):
            split.gender_rank = int(tds[6].text)
        if not (tds[7].text == "--:--" or tds[7].text == "" or tds[7].text == "--"):
            split.overall_rank = int(tds[7].text)
        return split


class SportStatsScraper:
    def __init__(self, env):
        self.url_template = "http://tracker.ironman.com/sportstatsv2/ironman/index.xhtml?raceid={race_id}&bib={bib}"
        self.race_id_column = "sportstats_race_id"
        if env == "DEV":
            self.browser = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs')
        elif env == "PROD":
            # TODO: set the path of phantomjs & logs
            self.browser = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs',
                                               service_log_path='/srv/www/[path to node server]/logs/ghostdriver.log')

    def close(self):
        # self.browser.close()
        return

    def scrape_athlete(self, new_url, bib, athlete_name):
        try:
            athlete = Athlete()
            self.browser.get(new_url)
            element = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, "dropdown_content")))
            page = self.browser.page_source
            soup = BeautifulSoup(page)
            # print athlete_div
            athlete_soup = soup.find(id="dropdown_content")

            # when bib or raceid not found:
            # <div id="resultForm:dataErrors">

            self.scrape_athlete_info(soup, athlete)
            self.scrape_athlete_splits(soup, athlete)
        finally:
            return athlete

    def scrape_athlete_info(self, soup, athlete):
        athlete.bib = soup.find("span", {"class": "bibnumber"}).text
        first_name = soup.find("span", {"class": "firstname"}).text
        last_name = soup.find("span", {"class": "lastname"}).text
        athlete.name = (first_name + " " + last_name).replace("'", "''")

        data_trs = soup.find_all("tr", {"data-ri": "0"})
        if data_trs:
            time_tr = data_trs[0]
            tds = time_tr.find_all("td")
            swim_td = tds[5]
            swim_time = swim_td.div.text.strip()
            if swim_time:
                athlete.swim_time = swim_time

            bike_td = tds[6]
            bike_time = bike_td.div.text.strip()
            if bike_time:
                athlete.bike_time = bike_time

            run_td = tds[7]
            run_time = run_td.div.text.strip()
            if run_time:
                athlete.run_time = run_time

            finish_td = tds[8]
            overall_time = finish_td.div.text.strip()
            if overall_time:
                athlete.overall_time = overall_time

            trans_div = soup.find(id="transition_info_holder")
            if trans_div:
                trans_tbody = trans_div.tbody
                t1_tr = trans_tbody.contents[0]
                t1_time = t1_tr.contents[1].text.strip()
                if t1_time:
                    athlete.t1_time = t1_time
                t2_tr = trans_tbody.contents[1]
                t2_time = t2_tr.contents[1].text.strip()
                if t2_time:
                    athlete.t2_time = t2_time

            info_tr = data_trs[1]
            tds = info_tr.find_all("td")
            category = tds[0].text.strip()
            athlete.division = category
            country = tds[1].text.strip()
            if len(country) and country != "unknown":
                athlete.country = country

        residence_text = soup.find(text="Residence")
        if residence_text:
            residence_tr = residence_text.parent.parent
            residence = residence_tr.contents[3].text.strip()
            if len(residence):
                athlete.residence = residence

        occupation_text = soup.find(text="Occupation")
        if occupation_text:
            occupation_tr = occupation_text.parent.parent
            occupation = occupation_tr.contents[3].text.strip()
            if len(occupation):
                athlete.occupation = occupation

        finish_tr = soup.find("tr", {"class": "ui-widget-content ui-datatable-odd bold_red"})
        if not finish_tr:
            finish_tr = soup.find("tr", {"class": "ui-widget-content ui-datatable-even bold_red"})
        if finish_tr:
            total_time = finish_tr.contents[4].text.strip()
            if total_time:
                athlete.overall_time = total_time

            overall_rank = finish_tr.contents[5].text.strip()
            if overall_rank:
                athlete.overall_rank = overall_rank

            gender_rank = finish_tr.contents[6].text.strip()
            if gender_rank:
                athlete.gender_rank = gender_rank

            division_rank = finish_tr.contents[7].text.strip()
            if division_rank:
                athlete.division_rank = division_rank

        rank_totals = soup.find(id="raceTotals")
        if rank_totals:
            race_total_div = rank_totals.contents[3]
            race_total = race_total_div.contents[3].text
            if race_total:
                athlete.overall_total = race_total

            gender_total_div = rank_totals.contents[5]
            gender_total = gender_total_div.contents[3].text
            if gender_total:
                athlete.gender_total = gender_total

            division_total_div = rank_totals.contents[7]
            division_total = division_total_div.contents[3].text
            if division_total:
                athlete.division_total = division_total

    def scrape_athlete_splits(self, soup, athlete):
        splits_div = soup.find(id="splits_info_holder")
        if not splits_div:
            return
        splits_tbody = splits_div.tbody
        split_trs = splits_tbody.find_all("tr")
        for tr in split_trs:
            # print tr
            if 'bold_red' in tr.attrs['class']:
                continue
            if 'hidden' in tr.attrs['class']:
                continue
            # check if totals column
            totals_column = 0
            if 'bold' in tr.attrs['class']:
                totals_column = 1
            split_tds = tr.find_all("td")
            split = Split()
            split_name = split_tds[0].text.strip()
            if totals_column:
                split.type = split_name.lower()
                split.name = "Total"
            else:
                split.type = split_name.split()[0].lower()
                split.name = split_name
            split_distance = split_tds[1].text.strip()
            if len(split_distance):
                split.distance = split_distance
            split_split_time = split_tds[2].text.strip()
            if len(split_split_time):
                split.split_time = split_split_time
            split_pace = split_tds[3].text.strip()
            if len(split_pace):
                split.pace = split_pace
            split_race_time = split_tds[4].text.strip()
            if len(split_race_time):
                split.race_time = split_race_time
            split_overall_rank = split_tds[5].text.strip()
            if len(split_overall_rank):
                split.overall_rank = split_overall_rank
            split_gender_rank = split_tds[6].text.strip()
            if split_gender_rank:
                split.gender_rank = split_gender_rank
            split_division_rank = split_tds[7].text.strip()
            if len(split_division_rank):
                split.division_rank = split_division_rank
            split_time_of_day = split_tds[8].text.strip()
            if len(split_time_of_day):
                split.time_of_day = split_time_of_day
            athlete.add_split(split)


class RaceScraper:
    def __init__(self, db_host, db_user, db_password, db_name, env):
        self.db = pymysql.connect(host=db_host,
                                  user=db_user,
                                  passwd=db_password,
                                  db=db_name)
        # self.scraper = scraper
        self.env = env
        self.scraper = None
        self.current_athlete = Athlete()
        self.logger = logging.getLogger('race_scraper')
        self.init_logger(self.env)

    def init_logger(self, env):
        path = ''
        if env == 'DEV':
            path = "./race_scraper.log"
        elif env == 'PROD':
            # TODO: set the path of logs
            path = "./race_scraper.log"
            # path = "/srv/www/api.triathletetracker.com/logs/race_scraper.log"
        # hdlr = logging.FileHandler(path)
        hdlr = logging.handlers.TimedRotatingFileHandler(path, 'midnight')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.DEBUG)

    def scrape_races_running(self):
        # get races currently running
        self.logger.debug("Scraping started.")
        select_cur = self.db.cursor()
        race_sql = "SELECT race_id, year, name, scraper_type from races where is_running = 1"
        select_cur.execute(race_sql)
        races = select_cur.fetchall()
        # loop
        if races:
            for r in races:
                # scrape
                race_id = r[0]
                race_year = str(r[1])
                race_name = str(r[2])
                scraper_type = r[3]
                if scraper_type == 0:
                    self.scraper = NewAthleteScraper(self.env)
                elif scraper_type == 1:
                    self.scraper = SportStatsScraper(self.env)
                self.logger.debug("%s %s: Scraping started." % (race_year, race_name))
                try:
                    self.scrape_race(race_id, race_year, race_name)
                    self.logger.debug("%s %s: Scraping finished" % (race_year, race_name))
                except Exception, e:
                    self.logger.error("%s %s - %s" % (race_year, race_name, e))
        self.logger.debug("Scraping finished.")

    def scrape_race(self, race_id, race_year, race_name, bib=0):
        select_cur = self.db.cursor()
        sql = "SELECT %s FROM races where race_id = %s" % (self.scraper.race_id_column, race_id)
        select_cur.execute(sql)
        result = select_cur.fetchone()
        scraper_race_id = 0
        if result[0] is None:
            self.logger.error("No scraper race id %s in database!" % race_id)
            self.scraper.close()
            return
        scraper_race_id = str(result[0])
        scraper_url = ""
        if scraper_race_id > 0:
            scraper_url = self.scraper.url_template.replace("{race_id}", scraper_race_id)
        if bib == 0:
            sql = "SELECT bib, athlete_id, name FROM athletes where race_id = %s order by bib" % race_id
            select_cur.execute(sql)
            athlete_count = select_cur.rowcount
            self.logger.debug("%s %s: %s athletes found." % (race_year, race_name, athlete_count))
            results = select_cur.fetchall()
            for row in results:
                bib = str(row[0])
                athlete_id = int(row[1])
                url = scraper_url.replace("{bib}", bib)
                athlete_name = str(row[2])
                # self.logger.debug("Checking %s bib %s." % (athlete_name, bib))
                self.logger.debug("%s %s: Scraping started." % (bib, athlete_name))
                try:
                    athlete = self.scraper.scrape_athlete(url, bib, athlete_name)
                    if athlete.bib is not None:
                        self.save_athlete(athlete_id, athlete, race_id, bib)
                        self.logger.debug("%s %s: Scraping finished." % (bib, athlete_name))
                except Exception, e:
                    self.logger.error("%s %s - %s" % (race_year, race_name, e))

        else:
            sql = "SELECT bib, athlete_id FROM athletes where race_id = %s and bib = %s" % (race_id, bib)
            select_cur.execute(sql)
            result = select_cur.fetchone()
            bib = str(result[0])
            athlete_id = int(result[1])
            url = scraper_url.replace("{bib}", bib)
            athlete = self.scraper.scrape_athlete(url)
            if athlete.bib is not None:
                self.save_athlete(athlete_id, athlete, race_id, bib)
        self.scraper.close()

    def get_athlete(self, athlete_id):
        athlete = Athlete()
        sql = "SELECT * from athletes where athlete_id = %s" % athlete_id
        select_cur = self.db.cursor()
        select_cur.execute(sql)
        result = select_cur.fetchone()
        if result:
            athlete.name = result[4]
            athlete.division = result[5]
            athlete.residence = result[6]
            athlete.country = result[7]
            athlete.occupation = result[8]
            athlete.division_rank = result[9]
            athlete.division_total = result[10]
            athlete.overall_rank = result[11]
            athlete.overall_total = result[12]
            athlete.gender_rank = result[13]
            athlete.gender_total = result[14]
            athlete.swim_time = result[15]
            athlete.t1_time = result[16]
            athlete.bike_time = result[17]
            athlete.t2_time = result[18]
            athlete.run_time = result[19]
            athlete.overall_time = result[20]
        return athlete

    def get_split(self, race_id, athlete_id, sequence):
        split = Split()
        sql = "SELECT " \
              "split_id," \
              "sequence," \
              "type," \
              "name," \
              "distance," \
              "split_time," \
              "race_time," \
              "time_of_day," \
              "pace," \
              "division_rank," \
              "overall_rank," \
              "gender_rank" \
              " from splits where race_id = %s and athlete_id = %s and sequence = %s" % (race_id, athlete_id, sequence)
        select_cur = self.db.cursor()
        select_cur.execute(sql)
        result = select_cur.fetchone()
        if result:
            split.split_id = result[0]
            split.sequence = result[1]
            split.type = result[2]
            split.name = result[3]
            split.distance = result[4]
            split.split_time = result[5]
            split.race_time = result[6]
            split.time_of_day = result[7]
            split.pace = result[8]
            split.division_rank = result[9]
            split.overall_rank = result[10]
            split.gender_rank = result[11]
        return split

    def save_athlete(self, athlete_id, athlete, race_id, bib):
        updated = 0
        current_athlete = self.get_athlete(athlete_id)
        update_sql = []

        self.build_update_sql(update_sql, current_athlete.name, athlete.name, "name")

        self.build_update_sql(update_sql, current_athlete.division, athlete.division, "division")

        self.build_update_sql(update_sql, current_athlete.residence, athlete.residence, "residence")

        self.build_update_sql(update_sql, current_athlete.country, athlete.country, "country")

        self.build_update_sql(update_sql, current_athlete.occupation, athlete.occupation, "occupation")

        self.build_update_sql(update_sql, current_athlete.division_rank, athlete.division_rank, "division_rank", 0)

        self.build_update_sql(update_sql, current_athlete.division_total, athlete.division_total, "division_total", 0)

        self.build_update_sql(update_sql, current_athlete.overall_rank, athlete.overall_rank, "overall_rank", 0)

        self.build_update_sql(update_sql, current_athlete.overall_total, athlete.overall_total, "overall_total", 0)

        self.build_update_sql(update_sql, current_athlete.gender_rank, athlete.gender_rank, "gender_rank", 0)

        self.build_update_sql(update_sql, current_athlete.gender_total, athlete.gender_total, "gender_total", 0)

        self.build_update_sql(update_sql, current_athlete.swim_time, athlete.swim_time, "swim_time")

        self.build_update_sql(update_sql, current_athlete.t1_time, athlete.t1_time, "t1_time")

        self.build_update_sql(update_sql, current_athlete.bike_time, athlete.bike_time, "bike_time")

        self.build_update_sql(update_sql, current_athlete.t2_time, athlete.t2_time, "t2_time")

        self.build_update_sql(update_sql, current_athlete.run_time, athlete.run_time, "run_time")

        self.build_update_sql(update_sql, current_athlete.overall_time, athlete.overall_time, "overall_time")

        if len(update_sql) > 0:
            update_vars = ', '.join(update_sql)
            sql = "UPDATE athletes SET %s WHERE athlete_id = %s" % (update_vars, athlete_id)
            insert_cur = self.db.cursor()
            insert_cur.execute(sql)
            self.db.commit()
            updated = 1

        # insert or update splits
        if len(athlete.splits) > 0:
            for split in athlete.splits:
                update_sql = []
                current_split = self.get_split(race_id, athlete_id, split.sequence)
                if current_split.split_id:
                    # split exists, update
                    if current_split.type != split.type:
                        self.build_update_sql(update_sql, current_split.type, split.type, "`type`")
                    if current_split.name != split.name:
                        self.build_update_sql(update_sql, current_split.name, split.name, "name")
                    if current_split.distance != split.distance:
                        self.build_update_sql(update_sql, current_split.distance, split.distance, "distance")
                    if current_split.split_time != split.split_time:
                        self.build_update_sql(update_sql, current_split.split_time, split.split_time, "split_time")
                    if current_split.race_time != split.race_time:
                        self.build_update_sql(update_sql, current_split.race_time, split.race_time, "race_time")
                    if current_split.time_of_day != split.time_of_day:
                        self.build_update_sql(update_sql, current_split.time_of_day, split.time_of_day, "time_of_day")
                    if current_split.pace != split.pace:
                        self.build_update_sql(update_sql, current_split.pace, split.pace, "pace")
                    if current_split.division_rank != split.division_rank:
                        self.build_update_sql(update_sql, current_split.division_rank, split.division_rank,
                                              "division_rank")
                    if current_split.overall_rank != split.overall_rank:
                        self.build_update_sql(update_sql, current_split.overall_rank, split.overall_rank,
                                              "overall_rank")
                    if current_split.gender_rank != split.gender_rank:
                        self.build_update_sql(update_sql, current_split.gender_rank, split.gender_rank, "gender_rank")

                    if len(update_sql) > 0:
                        update_vars = ', '.join(update_sql)
                        sql = "UPDATE splits SET %s WHERE split_id = %s" % (update_vars, current_split.split_id)
                        update_cur = self.db.cursor()
                        update_cur.execute(sql)
                        sql = "UPDATE athletes set last_updated = now() where athlete_id = %s" % athlete_id
                        update_cur.execute(sql)
                        self.db.commit()
                        updated = 1
                else:
                    # split doesn't exist, insert
                    distance = "'%s'" % split.distance if split.distance else "null"
                    split_time = "'%s'" % split.split_time if split.split_time else "null"
                    race_time = "'%s'" % split.race_time if split.race_time else "null"
                    pace = "'%s'" % split.pace if split.pace else "null"
                    division_rank = "%s" % split.division_rank if split.division_rank else "null"
                    overall_rank = "%s" % split.overall_rank if split.overall_rank else "null"
                    gender_rank = "%s" % split.gender_rank if split.gender_rank else "null"

                    insert_sql = "INSERT INTO splits " \
                                 "(race_id, athlete_id, sequence, type, name, distance, split_time, " \
                                 "race_time, pace, division_rank, overall_rank, gender_rank) " \
                                 "VALUES (%s, %s, %s, '%s', '%s', %s, %s, %s, %s, %s, %s, %s)" \
                                 % (race_id, athlete_id, split.sequence, split.type, split.name, distance, split_time,
                                    race_time, pace, division_rank, overall_rank, gender_rank)
                    insert_cur = self.db.cursor()
                    insert_cur.execute(insert_sql)
                    sql = "UPDATE athletes set last_updated = now() where athlete_id = %s" % athlete_id
                    update_cur = self.db.cursor()
                    update_cur.execute(sql)
                    self.db.commit()
                    updated = 1

        if updated:
            self.logger.debug("%s %s: CHANGES SAVED." % (bib, athlete.name))
        else:
            self.logger.debug("%s %s: No changes found." % (bib, athlete.name))

    def build_update_sql(self, sql_list, current_prop, new_prop, field_name, is_string=1):
        if new_prop == '': new_prop = None
        if isinstance(new_prop, str) or isinstance(new_prop, unicode): new_prop = new_prop.strip()
        if isinstance(current_prop, int): current_prop = str(current_prop)
        if isinstance(current_prop, str): current_prop = current_prop.decode('unicode-escape')
        if current_prop != new_prop:
            sql = "%s = " % field_name
            if new_prop:
                if is_string:
                    sql += "'%s'" % new_prop
                else:
                    sql += "%s" % new_prop
            else:
                sql += "null"
            sql_list.append(sql)


def main():
    # TODO: set db settings
    db_host = "XXX.XXX.XX.XXX"
    db_user = "marc"
    db_password = "XXXXX"

    env = 'PROD'
    # env = 'DEV'

    if env == "DEV":
        db_name = "triathlete_tracker_test"
    else:
        db_name = "triathlete_tracker"

    app = RaceScraper(db_host, db_user, db_password, db_name, env)
    app.scrape_races_running()


if __name__ == '__main__':
    main()
    print "done."
