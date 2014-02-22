import re
from collections import defaultdict

def make_timex(tid, type, val, verbose=False):
    if type == 'DATE':
        date_props = parse_date_str(str(val))
        if not date_props:
            if verbose:
                import sys
                sys.stderr.write('Warning: Could not parse date string ' \
                                 '{} -- for tid:{} {}\n'.format(val, tid, type))
                sys.stderr.flush()

        else:
            return Date(tid,
                        date_props['year'],
                        date_props['month'],
                        date_props['day'])
    elif type == 'TIME':
        time_props = parse_time_str(val)
        if not time_props:
            if verbose:
                import sys
                sys.stderr.write('Warning: Could not parse time string ' \
                                 '{} -- for tid:{} {}\n'.format(val, tid, type))
                sys.stderr.flush()

        else:
            return Time(tid,
                        year=time_props['year'],
                        month=time_props['month'],
                        day=time_props['day'],
                        hour=time_props['hour'],
                        minute=time_props['minute'],
                        second=time_props['second'],
                        interval=time_props['interval'])
   
    elif verbose:
        import sys
        sys.stderr.write('Warning: Could not parse timex string ' \
                         '{} -- for tid:{} {}\n'.format(val, tid, type))
        sys.stderr.flush()


def parse_date_str(date_str):
    m = re.match(r'^(\d\d\d\d|XXXX)-(\d\d|XX)-(\d\d|XX)$', date_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['year'] = m.group(1) if m.group(1) != 'XXXX' else None
        datum['month'] = m.group(2) if m.group(2) != 'XX' else None
        datum['day'] = m.group(3) if m.group(3) != 'XX' else None
        return datum

    m = re.match(r'^(\d\d\d\d|XXXX)-(\d\d|XX)$', date_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['year'] = m.group(1) if m.group(1) != 'XXXX' else None
        datum['month'] = m.group(2) if m.group(2) != 'XX' else None
        return datum

    m = re.match(r'^(\d\d\d\d)$', date_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['year'] = m.group(1)
        return datum
  

    return None

def parse_time_str(time_str):
    m = None
    m = re.match(r'^T(MO|AF|EV|NI)$', time_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['interval'] = m.group(1)
        return datum
    m = None
    m = re.match(r'^(....)-(..)-(..)T(MO|AF|EV|NI)$', time_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['year'] = m.group(1) if m.group(1) != 'XXXX' else None
        datum['month'] = m.group(2) if m.group(2) != 'XX' else None
        datum['day'] = m.group(3) if m.group(3) != 'XX' else None
        datum['interval'] = m.group(4)
        return datum

    m = re.match(r'^(\d\d\d\d|XXXX)-(\d\d|XX)-(\d\d|XX)T(\d\d):(\d\d)$', time_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['year'] = m.group(1) if m.group(1) != 'XXXX' else None
        datum['month'] = m.group(2) if m.group(2) != 'XX' else None
        datum['day'] = m.group(3) if m.group(3) != 'XX' else None
        datum['hour'] = m.group(4)
        datum['minute'] = m.group(5)
        return datum

    m = re.match(r'^(\d\d\d\d|XXXX)-(\d\d|XX)-(\d\d|XX)T(\d\d)$', time_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['year'] = m.group(1) if m.group(1) != 'XXXX' else None
        datum['month'] = m.group(2) if m.group(2) != 'XX' else None
        datum['day'] = m.group(3) if m.group(3) != 'XX' else None
        datum['hour'] = m.group(4)
        return datum
 
    
    m = re.match(r'^T(\d\d):(\d\d)$', time_str)
    if m:
        datum = defaultdict(lambda: None)
        datum['hour'] = m.group(1)
        datum['minute'] = m.group(2)
        return datum

    else:
        print 'STRING FAILED: {}'.format(time_str)
#


    return None

class Date:
    def __init__(self, tid, year, month, day):
        self.tid = tid
        self.year = year
        self.month = month
        self.day = day

    def __str__(self):
        
        if self.year and self.month and self.day:
            return '<DATE \'{}-{}-{}\'>'.format(self.year,
                                                self.month,
                                                self.day)
        
        elif self.year and self.month and not self.day:
            return '<DATE \'{}-{}\'>'.format(self.year,
                                             self.month)
        
        elif self.year and not self.month and not self.day:
            return '<DATE \'{}\'>'.format(self.year)

        elif not self.year and self.month and self.day:
            return '<DATE \'XXXX-{}-{}\'>'.format(self.month,
                                                  self.day)
        
        elif not self.year and self.month and not self.day:
            return '<DATE \'XXXX-{}\'>'.format(self.month)
        
        
        else: return str(self.__key())

    def __repr__(self):
        return str(self)

    def __key(self):
        return (self.tid,
                self.year,
                self.month,
                self.day)

    def __eq__(self, o):
        if isinstance(o, Date):
            return self.__key() == o.__key()
        else:
            return False
    def __hash__(self):
        return hash(self.__key())

class Time:
    def __init__(self, tid, year=None, month=None, day=None, hour=None, minute=None, second=None, interval=None):
        self.tid = tid
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.interval = interval

    def __str__(self):
        if self.day:
            if self.interval:
                year = self.year if self.year else 'XXXX'
                month = self.month if self.month else 'XX'
                return '<TIME \'{}-{}-{}T{}\'>'.format(year,
                                                       month,
                                                       self.day,
                                                       self.interval)
            else:
                year = self.year if self.year else 'XXXX'
                month = self.month if self.month else 'XX'
                day = self.day if self.day else 'XX'
                if self.minute:
                    return '<TIME \'{}-{}-{}T{}:{}\'>'.format(year,
                                                           month,
                                                           day,
                                                           self.hour,
                                                           self.minute)
                else:
                    return '<TIME \'{}-{}-{}T{}\'>'.format(year,
                                                           month,
                                                           day,
                                                           self.hour)


        if not self.year and not self.month and not self.day:
            if self.interval:
                return '<TIME \'T{}\'>'.format(self.interval)
            elif self.hour and self.minute:
                return '<TIME \'T{}:{}\'>'.format(self.hour, self.minute)
      
        
        return 'BROKEN'
        #if self.month and self.day and not self.interval:
        #    year = self.year if self.year else 'XXXX'
        #    month = self.month if self.month else 'XX'
        #    day = self.day if self.day else 'XX'
        #    return '<TIME \'{}-{}-{}T{}\'>'.format(year,
        #                                           month,
        #                                           day)

               
        
#        year = self.year if self.year != None else 'XXXX'
#        month = self.month if self.month != None else 'XX'
#        day = self.day if self.day != None else 'XX'
#        hour = self.hour if self.hour != None else 'XX'
#        minute = self.minute if self.minute != None else 'XX'
#        second = self.second if self.second != None else 'XX'
#        interval = self.interval if self.interval != None else 'XX'
#        return 'Time {}-{}-{} T{}:{}:{} {}'.format(year,
#                                                   month,
#                                                   day,
#                                                   hour,
#                                                   minute,
#                                                   second,
#                                                   interval)
    def __repr__(self):
        return str(self)

    def __key(self):
        return (self.tid,
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.interval)

    def __eq__(self, o):
        if isinstance(o, Time):
            return self.__key() == o.__key()
        else:
            return False
    def __hash__(self):
        return hash(self.__key())
