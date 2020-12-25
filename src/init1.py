#!C:/Users/lx615/AppData/Local/Programs/Python/Python38-32/python

#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import mysql.connector
import matplotlib
matplotlib.use('Agg') #constrain GUI dynamic plotting, in case be killed by OS
import matplotlib.pyplot as plt
from io import BytesIO #IO Byte streamline
import base64 #de/encoding


#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = mysql.connector.connect(host='localhost',
                               port=8889,
                               user='root',
                               password='root',
                               database='air_ticket')

#Helper function for making pie plot
def make_autopct(values):
    def my_autopct(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        # the number and ratio for the pie chart
        return '{p:.2f}%  ({v:d})'.format(p=pct,v=val)
    return my_autopct

#making the pie chart plot
def make_pie(username, index, value):
    plt.figure(figsize=(7,6.5))
    plt.pie(value, labels=index, autopct=make_autopct(value))
    plt.title("Pie: Your Spending in the Last 6 Months")
    plt.legend(loc='upper left')
    output_path = './templates/pic/'+username+'_pie.png'
    plt.savefig(output_path)
    return output_path

#making the bar chart plot
def make_bar(username, index, value):
    plt.figure(figsize=(7,6.5))
    plt.bar(index, height=value)
    plt.title("Bar: Your Spending in the Last 6 Months")
    plt.ylabel("Spending")
    plt.xlabel("Month")
    output_path = './templates/pic/'+username+'_bar.png'
    plt.savefig(output_path)
    return output_path
        
#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define a route to initial home page allowing general research
@app.route('/flight_search')
def flight_search():
    cursor = conn.cursor()
    #extract all existing arrival_airport
    query = "SELECT DISTINCT arrival_airport FROM flight"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()
    #extract all existing departure_airport
    query = "SELECT DISTINCT departure_airport FROM flight"
    cursor.execute(query)
    departure_airport = cursor.fetchall()
    #extract all existing arrival_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT arrival_airport FROM flight)"
    cursor.execute(query)
    arrival_city = cursor.fetchall()
    #extract all existing departure_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT departure_airport FROM flight)"
    cursor.execute(query)
    departure_city = cursor.fetchall()

    cursor.close()
    return render_template('flight_search.html', departure_city=departure_city,
                                                 departure_airport=departure_airport,
                                                 arrival_city=arrival_city,
                                                 arrival_airport=arrival_airport,
                                                 )

@app.route('/search', methods=['GET','POST'])
def search():
    if request.method == 'POST':
        #grab information based on customer's flight search selection
        departure_city = request.form['departure_city']
        departure_airport = request.form['departure_airport']
        arrival_city = request.form['arrival_city']
        arrival_airport = request.form['arrival_airport']
        flight_date = request.form['flight_date']
        
        flag1= bool(departure_city != "all")
        flag2 = bool(departure_airport != "all")
        flag3 = bool(arrival_city != "all")
        flag4 = bool(arrival_airport != "all")
        flag5 = bool(flight_date != "")
        if (not flag1 and not flag2 and not flag3 and not flag4 and not flag5):
            error = "At least 1 field should be specified!"
            return render_template('search_result.html', error=error)
        else:
            sub1 = ' departure_airport IN (SELECT airport_name FROM airport WHERE airport_city=\"{}\") '.format(departure_city)
            sub2 = ' departure_airport = \"{}\" '.format(departure_airport)
            sub3 = ' arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city=\"{}\") '.format(arrival_city)
            sub4 = ' arrival_airport =\"{}\" '.format(arrival_airport)
            sub5 = ' DATE(departure_time) = DATE(\"{}\") '.format(flight_date)
            # recall that: boolen * string = string if boolen=True, or "" if boolen=False
            merged_sub = list(filter(None,[flag1*sub1, flag2*sub2, flag3*sub3, flag4*sub4, flag5*sub5]))
            query = "SELECT * FROM flight WHERE " + " AND ".join(merged_sub) + " AND status = 'Upcoming' "
            cursor = conn.cursor()
            cursor.execute(query)
            search = cursor.fetchall()
            cursor.close()
            return render_template('search_result.html', search=search)
    
#Define route for flight status check
@app.route('/flight_status')
def flight_status():
    return render_template('flight_status.html')

#Check the status of a flight customer intend to inspect
@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        flight_number = request.form['flight_number']
        arrival_date = request.form['arrival_date']
        departure_date = request.form['departure_date']
        if (not arrival_date and not departure_date and not flight_number): # all three fields empty, not allowed
            error = "At least 1 field should be specified!"
            return render_template('flight_status.html', error = error)
        else: # valid to check for status:
            flag1 = bool(flight_number)
            flag2 = bool(arrival_date)
            flag3 = bool(departure_date)
            sub1 = " flight_num = \'{}\' ".format(flight_number)
            sub2 = " DATE(arrival_time) = DATE(\'{}\') ".format(arrival_date)
            sub3 = " DATE(departure_time) = DATE(\'{}\') ".format(departure_date)
            # recall that: boolen * string = string if boolen=True, or "" if boolen=False
            merged_sub = list(filter(None,[flag1*sub1, flag2*sub2, flag3*sub3]))
            query = "SELECT airline_name, flight_num, departure_time, arrival_time, status FROM flight WHERE " + " AND ".join(merged_sub)
            cursor = conn.cursor()
            cursor.execute(query)
            status = cursor.fetchall()
            cursor.close()
            return render_template('status_result.html', status=status)
    
#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    role = request.form['identity']
    username = request.form['username']
    password = request.form['password']

    cursor = conn.cursor()
    if role == 'customer':
        query = "SELECT * FROM customer WHERE email = \'{}\' and password = MD5(\'{}\') "
#        query = "SELECT * FROM customer WHERE email = \'{}\' and password = \'{}\' "
    elif role == 'booking_agent':
        query = "SELECT * FROM booking_agent WHERE email = \'{}\' and password = MD5(\'{}\') "
#        query = "SELECT * FROM booking_agent WHERE email = \'{}\' and password = \'{}\' "
    else:
        query = "SELECT * FROM airline_staff WHERE username = \'{}\' and password = MD5(\'{}\') "
#        query = "SELECT * FROM airline_staff WHERE username = \'{}\' and password = \'{}\' "
        
    cursor.execute(query.format(username, password))
    data = cursor.fetchone()
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        session['username'] = username
        session['identity'] = role
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Define route for customer register
@app.route('/customerRegister')
def customerRegister():
    return render_template('customer_register.html')

#Authenticates the register
@app.route('/customerRegisterAuth', methods=['GET', 'POST'])
def customerRegisterAuth():
    email = request.form['username']
    password = request.form['password']
    building_num = request.form['building number']
    street = request.form['street']
    city = request.form['city']
    state = request.form['state']
    name = request.form['name']
    phone = request.form['phone']
    birthday = request.form['birthday']
    pp_num = request.form['passport num']
    pp_expir_date = request.form['passport expir']
    pp_country = request.form['passport country']
    cursor = conn.cursor()
    query = "SELECT * FROM customer WHERE email = \'{}\'"
    cursor.execute(query.format(email))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('customer_register.html', error = error)
    else:
        ins = "INSERT INTO customer VALUES(\'{}\', \'{}\', MD5(\'{}\'), \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\' )"
#        ins = "INSERT INTO customer VALUES(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\' )"
        cursor.execute(ins.format(email, name, password, building_num, street, city,
                state, phone, pp_num, pp_expir_date, pp_country, birthday))
        conn.commit()
        cursor.close()
        flash("registered!")
        return render_template('index.html')
    
#Define route for booking agent register
@app.route('/agentRegister')
def agentRegister():
    return render_template('agent_register.html')

#Authenticates the register
@app.route('/agentRegisterAuth', methods=['GET', 'POST'])
def agentRegisterAuth():
    email = request.form['username']
    password = request.form['password']

    cursor = conn.cursor()
    query = "SELECT * FROM booking_agent WHERE email = \'{}\'"
    cursor.execute(query.format(email))
    data = cursor.fetchone()
    cursor.close()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('agent_register.html', error = error)
    else:
        #find an agent id for this new account
        cursor = conn.cursor()
        query = "SELECT MAX(booking_agent_id) FROM booking_agent; "
        cursor.execute(query)
        old_id = cursor.fetchone()
        cursor.close()
        if not old_id[0]: # no agent exists yet
            agent_id = 1
        else:
            agent_id = int(old_id[0]) + 1
        
        cursor = conn.cursor()
        ins = "INSERT INTO booking_agent VALUES(\'{}\', MD5(\'{}\'), \'{}\')"  
#        ins = "INSERT INTO booking_agent VALUES(\'{}\', \'{}\', \'{}\')" 
        cursor.execute(ins.format(email, password, agent_id))
        conn.commit()
        cursor.close()
        flash("registered!")
        return render_template('index.html')
    
#Define route for airline staff register
@app.route('/staffRegister')
def staffRegister():
    cursor = conn.cursor()
    query = "SELECT DISTINCT * FROM airline"
    cursor.execute(query)
    data = cursor.fetchall()
    
    return render_template('staff_register.html', airline_list=data)

#Authenticates the register
@app.route('/staffRegisterAuth', methods=['GET', 'POST'])
def staffRegisterAuth():
    email = request.form['username']
    password = request.form['password']
    first_name = request.form['first name']
    last_name = request.form['last name']
    birthday = request.form['birthday']
    airline = request.form['airline']

    cursor = conn.cursor()
    query = "SELECT * FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(email))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('staff_register.html', error = error)
    else:
        ins = "INSERT INTO airline_staff VALUES(\'{}\', MD5(\'{}\'), \'{}\', \'{}\', \'{}\', \'{}\')" 
#        ins = "INSERT INTO airline_staff VALUES(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')"
        cursor.execute(ins.format(email, password, first_name, last_name, birthday, airline))
        conn.commit()
        cursor.close()
        flash("registered!")
        return render_template('index.html')

#User homepage
@app.route('/home')
def home():
    username = session['username']
    identity = session['identity']
    
    if identity == 'customer':
        cursor = conn.cursor()
        query = "SELECT airline_name, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, status FROM purchases NATURAL JOIN (ticket NATURAL JOIN flight) WHERE customer_email = \'{}\' AND status = 'Upcoming' "
        cursor.execute(query.format(username))
        data1 = cursor.fetchall()
        cursor.close()#Added cursor close point#
        return render_template('home.html', username=username, identity=identity, upcoming=data1)
        
    elif identity == 'airline_staff':
        return render_template('home.html', username=username, identity=identity)
    
    else:
        return render_template('home.html', username=username, identity=identity)

#####################Customer Begin########################################
#Define a route for customer to search for a flight (and potential purchase later)
@app.route('/customer_flight_search')
def customer_flight_search():
    cursor = conn.cursor()
    #extract all existing arrival_airport
    query = "SELECT DISTINCT arrival_airport FROM flight"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()
    #extract all existing departure_airport
    query = "SELECT DISTINCT departure_airport FROM flight"
    cursor.execute(query)
    departure_airport = cursor.fetchall()
    #extract all existing arrival_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT arrival_airport FROM flight)"
    cursor.execute(query)
    arrival_city = cursor.fetchall()
    #extract all existing departure_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT departure_airport FROM flight)"
    cursor.execute(query)
    departure_city = cursor.fetchall()
    cursor.close()
    return render_template('customer_flight_search.html',
                                                departure_city=departure_city,
                                                departure_airport=departure_airport,
                                                arrival_city=arrival_city,
                                                arrival_airport=arrival_airport,
                                                )

@app.route('/customer_search', methods=['GET','POST'])
def customer_search():
    if request.method == 'POST':
        #grab information based on customer's flight search selection
        departure_city = request.form['departure_city']
        departure_airport = request.form['departure_airport']
        arrival_city = request.form['arrival_city']
        arrival_airport = request.form['arrival_airport']
        flight_date = request.form['flight_date']
        
        flag1= bool(departure_city != "all")
        flag2 = bool(departure_airport != "all")
        flag3 = bool(arrival_city != "all")
        flag4 = bool(arrival_airport != "all")
        flag5 = bool(flight_date != "")
        if (not flag1 and not flag2 and not flag3 and not flag4 and not flag5):
            error = "At least 1 field should be specified!"
            return render_template('customer_search_result.html', error=error)
        else:
            sub1 = " departure_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(departure_city)
            sub2 = ' departure_airport = \"{}\" '.format(departure_airport)
            sub3 = " arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(arrival_city)
            sub4 = ' arrival_airport =\"{}\" '.format(arrival_airport)
            sub5 = " DATE(departure_time) = DATE(\'{}\') ".format(flight_date)
            # recall that: boolen * string = string if boolen=True, or "" if boolen=False
            merged_sub = list(filter(None,[flag1*sub1, flag2*sub2, flag3*sub3, flag4*sub4, flag5*sub5]))
            query = "SELECT * FROM flight WHERE " + " AND ".join(merged_sub) + " AND status = 'Upcoming' "
            cursor = conn.cursor()
            cursor.execute(query)
            search = cursor.fetchall()
            available_seats = list()
            for flight in search:
                # (airline,flight_num) is primary key for a flight
                airline = flight[0]
                flight_num = flight[1]
                airplane_id_query = "SELECT airplane_id FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\'".format(airline, flight_num)
                cursor.execute(airplane_id_query)
                airplane_id = cursor.fetchone()[0] # get the airplane id for that flight
                total_query = "SELECT seats FROM airplane WHERE airline_name = \'{}\' AND airplane_id = \'{}\'".format(airline, airplane_id)
                cursor.execute(total_query)
                total = cursor.fetchone()[0] # find the total available seats for that air plane
                sold_query = "SELECT COUNT(*) FROM ticket WHERE airline_name = \'{}\' AND  flight_num = \'{}\'".format(airline, flight_num)
                cursor.execute(sold_query)
                sold = cursor.fetchone()[0] # find how many seats already sold for that flight
                available = int(total) - int(sold)
                available_seats.append(available) # record the available seats for this flight
            for i in range(len(search)): # add the available seats info for this flight we searched out
                # tuple is immutable, convert to list first
                original = list(search[i])
                original.append(available_seats[i])
                new = tuple(original)
                search[i] = new
            cursor.close()
            return render_template('customer_search_result.html', search=search)

#Purchase a ticket for a customer
@app.route('/customer_purchase', methods=['GET', 'POST'])
def customer_purchase():
    if request.method == "POST":
        airline = request.form['airline']
        flight_num = request.form['flight_num']
        username = session['username']
        cursor = conn.cursor()
        # Check if this customer has already bought a ticket for this flight
        # multiple purchases for the same flight is not allowed in our design
        multiple_purchase_query = "SELECT * FROM purchases NATURAL JOIN ticket WHERE customer_email=\'{}\' AND airline_name=\'{}\' AND flight_num=\'{}\'".format(username, airline, flight_num)
        cursor.execute(multiple_purchase_query)
        multiple_purchase = cursor.fetchone()
        if (multiple_purchase):
            warning = "Warning: Your have previously already purchased ticket for flight \"{}-{}\", no multiple purchases allowed!".format(airline,flight_num)
            flash(warning)
            return redirect(url_for('customer_flight_search'))
        # First, create a ticket for this customer's purchase
        ## need to know the so far biggest ticket number, and then plus 1 to it for new one
        ## ticket_id is primary key for a ticket, across different flight and airline
        ticket_number_query = "SELECT MAX(ticket_id) FROM ticket"
        cursor.execute(ticket_number_query)
        old_id = cursor.fetchone()
        if not old_id[0]: # no any ticket exists
            new_id = 1
        else:
            new_id = int(old_id[0]) + 1
        create_ticket_query = "INSERT INTO ticket VALUES (\'{}\', \'{}\', \'{}\')".format(new_id, airline, flight_num)
        cursor.execute(create_ticket_query)
        conn.commit()
        ## record the purchases record for that customer
        ## set booking_agent = NULL, purchase date is right now today
        purchase_record_query = "INSERT INTO purchases VALUES (\'{}\', \'{}\', NULL , DATE(NOW()) )".format(new_id, username )
        cursor.execute(purchase_record_query)
        conn.commit()
        cursor.close()
        flash("Your purchase has been processed! Thanks!")
        return redirect(url_for('home'))

@app.route('/customer_spending', methods=['GET', 'POST'])
def customer_spending():
    username = session['username']
    cursor = conn.cursor()
    last_year_query = "SELECT SUM(price) FROM purchases NATURAL JOIN ticket NATURAL JOIN flight  WHERE customer_email= \'{}\' AND purchase_date BETWEEN date_sub(DATE(NOW()), interval 1 year) AND DATE(NOW())".format(username)
    cursor.execute(last_year_query)
    last_year = cursor.fetchone()
    cursor.close()
    if not last_year:
        last_year = "0"
    else:
        last_year = last_year[0]
    # generate the default past 6 months spending data
    month_query = "SELECT YEAR(date_sub(DATE(NOW()), interval {} month)) as year , MONTH(date_sub(DATE(NOW()), interval {} month)) as month, SUM(price) FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE customer_email=\'{}\' AND YEAR(purchase_date)=YEAR(date_sub(DATE(NOW()), interval {} month))  AND MONTH(purchase_date)= MONTH(date_sub(DATE(NOW()), interval {} month))"
    month_query_list = [month_query.format("0","0",username, "0", "0"),
                                            month_query.format("1","1",username, "1", "1"),
                                            month_query.format("2","2",username, "2", "2"),
                                            month_query.format("3","3",username, "3", "3"),
                                            month_query.format("4","4",username, "4", "4"),
                                            month_query.format("5","5",username, "5", "5")] # query list to generate the past 6 months' monthly spending
    month_index = []
    month_spending = [0, 0, 0, 0, 0, 0]
    cursor = conn.cursor()
    for i,query in enumerate(month_query_list):
        cursor.execute(query)
        spending = cursor.fetchone()
        if spending[2]:
            month_spending[i] = int(spending[2])
        month_index.append(str(spending[0])+'-'+str(spending[1]))
    cursor.close()
    # open a "deceiving" ByteIO thread to generate the return make the url for plot
    img = BytesIO()
    fig, (ax1, ax2) = plt.subplots(2, figsize=(10,10))
    fig.suptitle('Past 6 Months Spending Track')
    ax1.bar(month_index, height=month_spending)
    ax1.set_xlabel('month')
    ax1.set_ylabel('amount of spending')
    ax2.pie(month_spending, labels=month_index, autopct=make_autopct(month_spending))
    fig.legend(loc='center right')
    fig.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('customer_spending.html', last_year=last_year, plot_url = plot_url)
        
        
@app.route('/customize_spending', methods=['GET', 'POST'])
def customize_spending():
    username = session['username']
    start = request.form['start_month']
    end = request.form['end_month']
    if ((not start) or (not end)): # both start/end month must be specified
        error = "Both starting month and ending month must be specified for customize track!"
        return render_template('customize_spending_failure.html', error=error)
    elif start > end:
        error = "starting month must be no later than ending month!"
        return render_template('customize_spending_failure.html', error=error)
    else:
        start_year, start_month = start[:4], start[-2:]
        end_year, end_month = end[:4], end[-2:]
        cursor = conn.cursor()
        total_query = "SELECT SUM(price) FROM purchases NATURAL JOIN ticket NATURAL JOIN flight  WHERE customer_email= \'{}\' AND (YEAR(purchase_date) BETWEEN \'{}\' AND \'{}\') AND (MONTH(purchase_date) BETWEEN \'{}\' AND \'{}\')".format(username,start_year, end_year,start_month,end_month)
        cursor.execute(total_query)
        total = cursor.fetchone()
        cursor.close()
        if not total:
            total = "0"
        else:
            total = total[0]
        # You have to append the "Day" 'xxxx-xx-01' to make this function works properly,
        # otherwise, the TIMESTAMPDIFF function returns None
        old_start, old_end = start, end
        start, end = start+'-01', end+'-01'
        
        cursor = conn.cursor()
        month_gap_query = "SELECT TIMESTAMPDIFF(MONTH, \'{}\', \'{}\')".format(start, end)
        cursor.execute(month_gap_query)
        month_gap = cursor.fetchone()[0]
        cursor.close()##-----！！！&&&##
        
        month_query = "SELECT YEAR(date_sub(DATE(\'{}\'), interval {} month)) as year , MONTH(date_sub(DATE(\'{}\'), interval {} month)) as month, SUM(price) FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE customer_email=\'{}\' AND YEAR(purchase_date)=YEAR(date_sub(DATE(\'{}\'), interval {} month))  AND MONTH(purchase_date)= MONTH(date_sub(DATE(\'{}\'), interval {} month))"
        month_query_list=[month_query.format(end,i,end,i,username,end,i,end,i) for i in range(month_gap+1)] # create the query for each individual customized range
        month_index = []
        month_spending = [0] * (month_gap+1)
        
        cursor = conn.cursor()
        for i,query in enumerate(month_query_list):
            cursor.execute(query)
            spending = cursor.fetchone()
            if spending[2]:
                month_spending[i] = int(spending[2])
            month_index.append(str(spending[0])+'-'+str(spending[1]))
        # open a "deceiving" ByteIO thread to generate the return make the url for plot
        cursor.close()
        
        img = BytesIO()
        fig, (ax1, ax2) = plt.subplots(2, figsize=(10,10))
        fig.suptitle('{} to {} Spending Track'.format(old_start,old_end))
        ax1.bar(month_index, height=month_spending)
        ax1.set_xlabel('month')
        ax1.set_ylabel('amount of spending')
        ax2.pie(month_spending, labels=month_index, autopct=make_autopct(month_spending))
        fig.legend(loc='center right')
        fig.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        return render_template('customize_spending.html', start_year=start_year, start_month=start_month, end_year=end_year, end_month=end_month, total=total, plot_url=plot_url)
#####################Customer End########################################
        

#####################Agent Begin########################################
#View all upcoming flights (default)
@app.route('/home/agent_view_flight')
def agent_view_flight():
    username = session['username']
    #use username to find booking agent id
    cursor = conn.cursor()
    query = "SELECT booking_agent_id FROM booking_agent WHERE email = \'{}\' ;"
    cursor.execute(query.format(username))
    agent_id = cursor.fetchone()
    cursor.close()
    
    #find all upcoming flights the agent ordered for customers
    query = "SELECT f.airline_name, f.flight_num, f.departure_airport, f.departure_time, " +\
            "f.arrival_airport, f.arrival_time, f.price, f.status, f.airplane_id, p.customer_email " +\
            "FROM purchases p, ticket t, flight f " +\
            "WHERE p.booking_agent_id = \'{}\' AND p.ticket_id = t.ticket_id AND " +\
            "t.airline_name = f.airline_name AND t.flight_num = f.flight_num AND " +\
            "f.status = 'Upcoming' ;"
    cursor = conn.cursor()
    cursor.execute(query.format(agent_id[0]))
    flights = cursor.fetchall()
    
    #extract all existing arrival_airport
    query = "SELECT DISTINCT arrival_airport FROM flight"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()
    
    #extract all existing departure_airport
    query = "SELECT DISTINCT departure_airport FROM flight"
    cursor.execute(query)
    departure_airport = cursor.fetchall()
    
    #extract all existing arrival_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT arrival_airport FROM flight)"
    cursor.execute(query)
    arrival_city = cursor.fetchall()
    
    #extract all existing departure_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT departure_airport FROM flight)"
    cursor.execute(query)
    departure_city = cursor.fetchall()
    
    #extract all the flight numbers
    query = "SELECT DISTINCT flight_num FROM flight ;"
    cursor.execute(query)
    flight_num = cursor.fetchall()
    cursor.close()
    return render_template('agent_view_flight.html', flights=flights,
                                                     arrival_airport=arrival_airport,
                                                     departure_airport=departure_airport,
                                                     arrival_city=arrival_city,
                                                     departure_city=departure_city,
                                                     flight_number=flight_num)
    
@app.route('/home/agent_view_flight/agent_customize_view', methods=['GET','POST'])
def agent_customize_view():
    if request.method == 'POST':
        username = session['username']
        #use username to find booking agent id
        cursor = conn.cursor()
        query = "SELECT booking_agent_id FROM booking_agent WHERE email = \'{}\' ;"
        cursor.execute(query.format(username))
        agent_id = cursor.fetchone()
        cursor.close()
        
        #grab information based on customer's flight search selection
        departure_city = request.form['departure_city']
        departure_airport = request.form['departure_airport']
        arrival_city = request.form['arrival_city']
        arrival_airport = request.form['arrival_airport']
        starting_date = request.form['starting_date']
        ending_date = request.form['ending_date']
        
        flag1= bool(departure_city != "all")
        flag2 = bool(departure_airport != "all")
        flag3 = bool(arrival_city != "all")
        flag4 = bool(arrival_airport != "all")
        flag5 = bool(starting_date != "" or ending_date != "")
        flag_start = bool(starting_date != "")
        flag_end = bool(ending_date != "")
        if (not flag1 and not flag2 and not flag3 and not flag4 and not flag5):
            error = "At least 1 field should be specified!"
            return render_template('agent_customize_view.html', error=error)
        else:
            sub1 = " f.departure_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(departure_city)
            sub2 = " f.departure_airport = \"{}\" ".format(departure_airport)
            sub3 = " f.arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(arrival_city)
            sub4 = " f.arrival_airport = \"{}\" ".format(arrival_airport)
            if (flag_start and flag_end):
                sub5 = "( DATE(f.departure_time) BETWEEN DATE(\'{}\') AND DATE(\'{}\') )".format(starting_date, ending_date)
            elif (flag_start and not flag_end):
                sub5 = "( DATE(f.departure_time) >= DATE(\'{}\') )".format(starting_date)
            elif (flag_end and not flag_start):
                sub5 = "( DATE(f.departure_time) <= DATE(\'{}\') )".format(ending_date)
            else:
                sub5 = "empty query"
            # recall that: boolen * string = string if boolen=True, or "" if boolen=False
            merged_sub = list(filter(None,[flag1*sub1, flag2*sub2, flag3*sub3, flag4*sub4, flag5*sub5]))
            query = "SELECT * FROM flight f, ticket t, purchases p WHERE " + " AND ".join(merged_sub)
            
            query += " AND p.booking_agent_id = \'{}\' AND p.ticket_id = t.ticket_id AND " +\
                     "t.airline_name = f.airline_name AND t.flight_num = f.flight_num ;"
            cursor = conn.cursor()
            cursor.execute(query.format(agent_id[0]))
            search = cursor.fetchall()
            cursor.close()
        return render_template('agent_customize_view.html', search=search)
    
#Define a route for agent to search for a flight (and potential purchase later)
@app.route('/home/agent_flight_search')
def agent_flight_search():
    cursor = conn.cursor()
    #extract all existing arrival_airport
    query = "SELECT DISTINCT arrival_airport FROM flight"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()
    #extract all existing departure_airport
    query = "SELECT DISTINCT departure_airport FROM flight"
    cursor.execute(query)
    departure_airport = cursor.fetchall()
    #extract all existing arrival_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT arrival_airport FROM flight)"
    cursor.execute(query)
    arrival_city = cursor.fetchall()
    #extract all existing departure_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT departure_airport FROM flight)"
    cursor.execute(query)
    departure_city = cursor.fetchall()
    cursor.close()
    return render_template('agent_flight_search.html', departure_city=departure_city,
                                                       departure_airport=departure_airport,
                                                       arrival_city=arrival_city,
                                                       arrival_airport=arrival_airport)

@app.route('/home/agent_search', methods=['GET','POST'])
def agent_search():
    if request.method == 'POST':
        #grab information based on customer's flight search selection
        departure_city = request.form['departure_city']
        departure_airport = request.form['departure_airport']
        arrival_city = request.form['arrival_city']
        arrival_airport = request.form['arrival_airport']
        flight_date = request.form['flight_date']
        
        flag1= bool(departure_city != "all")
        flag2 = bool(departure_airport != "all")
        flag3 = bool(arrival_city != "all")
        flag4 = bool(arrival_airport != "all")
        flag5 = bool(flight_date != "")
        if (not flag1 and not flag2 and not flag3 and not flag4 and not flag5):
            error = "At least 1 field should be specified!"
            return render_template('agent_search_result.html', error=error)
        else:
            sub1 = " departure_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(departure_city)
            sub2 = " departure_airport = \"{}\" ".format(departure_airport)
            sub3 = " arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(arrival_city)
            sub4 = " arrival_airport =\"{}\" ".format(arrival_airport)
            sub5 = " DATE(departure_time) = DATE(\'{}\') ".format(flight_date)
            # recall that: boolen * string = string if boolen=True, or "" if boolen=False
            merged_sub = list(filter(None,[flag1*sub1, flag2*sub2, flag3*sub3, flag4*sub4, flag5*sub5]))
            query = "SELECT * FROM flight WHERE status = 'Upcoming' AND " + " AND ".join(merged_sub)
            cursor = conn.cursor()
            cursor.execute(query)
            search = cursor.fetchall()
            available_seats = list()
            for flight in search:
                # (airline,flight_num) is primary key for a flight
                airline = flight[0]
                flight_num = flight[1]
                airplane_id_query = "SELECT airplane_id FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\'".format(airline, flight_num)
                cursor.execute(airplane_id_query)
                airplane_id = cursor.fetchone()[0] # get the airplane id for that flight
                total_query = "SELECT seats FROM airplane WHERE airline_name = \'{}\' AND airplane_id = \'{}\'".format(airline, airplane_id)
                cursor.execute(total_query)
                total = cursor.fetchone()[0] # find the total available seats for that air plane
                sold_query = "SELECT COUNT(*) FROM ticket WHERE airline_name = \'{}\' AND  flight_num = \'{}\'".format(airline, flight_num)
                cursor.execute(sold_query)
                sold = cursor.fetchone()[0] # find how many seats already sold for that flight
                available = int(total) - int(sold)
                available_seats.append(available) # record the available seats for this flight
            for i in range(len(search)): # add the available seats info for this flight we searched out
                # tuple is immutable, convert to list first
                original = list(search[i])
                original.append(available_seats[i])
                new = tuple(original)
                search[i] = new
            cursor.close()
            return render_template('agent_search_result.html', search=search)
        
@app.route('/home/agent_search/agent_select_customer', methods=['GET','POST'])
def agent_select_customer():
    if request.method == 'POST':
        #grab information based on agent's flight search selection
        airline = request.form['airline']
        flight_num = request.form['flight_num']
        
        #grab all the customer emails
        query = "SELECT DISTINCT email FROM customer"
        cursor = conn.cursor()
        cursor.execute(query)
        email = cursor.fetchall()
        cursor.close()
        return render_template('agent_select_customer.html', airline=airline,
                                                             flight_num=flight_num,
                                                             email=email)

#Purchase a ticket for a customer
@app.route('/home/agent_search/agent_purchase', methods=['GET', 'POST'])
def agent_purchase():
    if request.method == "POST":
        airline = request.form['airline']
        flight_num = request.form['flight_num']
        customer_email = request.form['email']
        username = session['username']
        
        # Check if this customer has already bought a ticket for this flight
        # multiple purchases for the same flight is not allowed in our design
        cursor = conn.cursor()
        multiple_purchase_query = "SELECT * FROM purchases NATURAL JOIN ticket " +\
                                  "WHERE customer_email=\'{}\' AND airline_name=\'{}\' " +\
                                  "AND flight_num=\'{}\' ;"
        cursor.execute(multiple_purchase_query.format(customer_email, airline, flight_num))
        multiple_purchase = cursor.fetchall()
        cursor.close()
        if (multiple_purchase):
            warning = "Warning: Your customer already had a ticket for flight \"{}-{}\", no multiple purchases allowed!"
            flash(warning.format(airline,flight_num))
            return redirect(url_for('agent_flight_search'))
        
        # First, create a ticket for this customer's purchase
        ## need to know the so far biggest ticket number, and then plus 1 to it for new one
        ## ticket_id is primary key for a ticket, across different flight and airline
        ticket_number_query = "SELECT MAX(ticket_id) FROM ticket"
        cursor = conn.cursor()
        cursor.execute(ticket_number_query)
        old_id = cursor.fetchone()
        cursor.close()
        if not old_id[0]: # no any ticket exists
            new_id = 1
        else:
            new_id = int(old_id[0]) + 1
        create_ticket_query = "INSERT INTO ticket VALUES (\'{}\', \'{}\', \'{}\') ;"
        cursor = conn.cursor()
        cursor.execute(create_ticket_query.format(new_id, airline, flight_num))
        conn.commit()
        cursor.close()
        
        ## find the agent id
        agent_id_query = "SELECT booking_agent_id FROM booking_agent WHERE email = \'{}\' ;"
        cursor = conn.cursor()
        cursor.execute(agent_id_query.format(username))
        agent_id = cursor.fetchone()
        cursor.close()
        
        ## record the purchases record for that customer
        purchase_record_query = "INSERT INTO purchases VALUES (\'{}\', \'{}\', \'{}\', DATE(NOW()) );"
        cursor = conn.cursor()
        cursor.execute(purchase_record_query.format(new_id, customer_email, agent_id[0]))
        conn.commit()
        cursor.close()
        flash("Your purchase has been processed! Thanks!")
        return redirect(url_for('agent_flight_search'))

#View commission (default display)
@app.route('/home/agent_view_commission')
def agent_view_commission():
    username = session['username']
    #use username to find booking agent id
    cursor = conn.cursor()
    query = "SELECT booking_agent_id FROM booking_agent WHERE email = \'{}\' ;"
    cursor.execute(query.format(username))
    agent_id = cursor.fetchone()
    cursor.close()
    #find total commission in the past 30 days
    query = "SELECT 0.1*SUM(f.price) " +\
            "FROM purchases p, ticket t, flight f " +\
            "WHERE p.booking_agent_id = \'{}\' AND p.ticket_id = t.ticket_id AND " +\
            "t.airline_name = f.airline_name AND t.flight_num = f.flight_num AND " +\
            "p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -30 DAY) ;"
    cursor = conn.cursor()
    cursor.execute(query.format(agent_id[0]))
    commission = cursor.fetchone()
    cursor.close()
    #find total tickets sold in the past 30 days
    query = "SELECT COUNT(*) " +\
            "FROM purchases p " +\
            "WHERE p.booking_agent_id = \'{}\' AND " +\
            "p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -30 DAY) ;"
    cursor = conn.cursor()
    cursor.execute(query.format(agent_id[0]))
    num_ticket = cursor.fetchone()
    cursor.close()
    #calculate the average commission
    average_commission = round(int(commission[0]) / int(num_ticket[0]), 2)
    
    return render_template('agent_view_commission.html', commission=commission,
                                                         num_ticket=num_ticket,
                                                         average_commission=str(average_commission))
    
@app.route('/home/agent_view_commission/agent_customize_commission', methods=['GET','POST'])
def agent_customize_commission():
    if request.method == 'POST':
        username = session['username']
        starting_date = request.form['starting_date']
        ending_date = request.form['ending_date']
        #starting date must be earlier
        if starting_date > ending_date:
            error = "Starting date must be earlier than ending date!"
            flash(error) 
            return redirect(url_for('agent_view_commission'))
        
        #use username to find booking agent id
        cursor = conn.cursor()
        query = "SELECT booking_agent_id FROM booking_agent WHERE email = \'{}\' ;"
        cursor.execute(query.format(username))
        agent_id = cursor.fetchone()
        cursor.close()
        
        #find total commission in selected period
        query = "SELECT 0.1*SUM(f.price) " +\
                "FROM purchases p, ticket t, flight f " +\
                "WHERE p.booking_agent_id = \'{}\' AND p.ticket_id = t.ticket_id AND " +\
                "t.airline_name = f.airline_name AND t.flight_num = f.flight_num AND " +\
                "(p.purchase_date BETWEEN \'{}\' AND \'{}\' ) ;"
        cursor = conn.cursor()
        cursor.execute(query.format(agent_id[0], starting_date, ending_date))
        commission = cursor.fetchone()
        cursor.close()
        #find total tickets sold in selected period
        query = "SELECT COUNT(*) " +\
                "FROM purchases p " +\
                "WHERE p.booking_agent_id = \'{}\' AND " +\
                "(p.purchase_date BETWEEN \'{}\' AND \'{}\' ) ;"
        cursor = conn.cursor()
        cursor.execute(query.format(agent_id[0], starting_date, ending_date))
        num_ticket = cursor.fetchone()
        cursor.close()
        
        return render_template('agent_customize_commission.html', commission=commission,
                                                                  num_ticket=num_ticket)
        
@app.route('/home/agent_top_customer')
def agent_top_customer():
    username = session['username']
    #use username to find booking agent id
    cursor = conn.cursor()
    query = "SELECT booking_agent_id FROM booking_agent WHERE email = \'{}\' ;"
    cursor.execute(query.format(username))
    agent_id = cursor.fetchone()
    cursor.close()
    
    #find top customers in past 6 months based on tickets sold
    query = "SELECT p.customer_email, COUNT(p.customer_email), c.name, c.phone_number, c.city, c.state, c.date_of_birth " +\
            "FROM purchases p, customer c " +\
            "WHERE p.booking_agent_id = \'{}\' AND p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -6 MONTH) " +\
            "AND p.customer_email = c.email " +\
            "GROUP BY p.customer_email " +\
            "ORDER BY COUNT(p.customer_email) DESC; "
    cursor = conn.cursor()
    cursor.execute(query.format(agent_id[0]))
    customer = []
    #scan the results to fetch <= top 5 customers if exist
    cust = cursor.fetchone()
    count = 1
    while cust and count <= 5:
        customer.append(list(cust))
        cust = cursor.fetchone()
        count += 1
    cursor.close()
    customer_ticket = tuple(customer)
    
    #find top customers in past 6 months based on commission earned
    query = "SELECT p.customer_email, 0.1 * SUM(f.price), c.name, c.phone_number, c.city, c.state, c.date_of_birth " +\
            "FROM purchases p, ticket t, flight f, customer c " +\
            "WHERE p.booking_agent_id = \'{}\' AND p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -6 MONTH) " +\
            "AND p.ticket_id = t.ticket_id AND t.airline_name = f.airline_name " +\
            "AND t.flight_num = f.flight_num AND p.customer_email = c.email " +\
            "GROUP BY p.customer_email ORDER BY SUM(f.price) DESC; "
    cursor = conn.cursor()
    cursor.execute(query.format(agent_id[0]))
    customer = []
    #scan the results to fetch <= top 5 customers if exist
    cust = cursor.fetchone()
    count = 1
    while cust and count <= 5:
        customer.append(list(cust))
        cust = cursor.fetchone()
        count += 1
    cursor.close()
    customer_commission = tuple(customer)
    
    x_ticket = [row[2] for row in customer_ticket]
    y_ticket = [int(row[1]) for row in customer_ticket]
    
    x_commission = [row[2] for row in customer_commission]
    y_commission = [float(row[1]) for row in customer_commission]
    
    img = BytesIO()
    fig, (ax1, ax2) = plt.subplots(2, figsize=(10,10))
    ax1.bar(x_ticket, height=y_ticket, width=0.2, color='lightgreen', edgecolor='blue')
    ax1.set_xlabel('customer')
    ax1.set_ylabel('ticket number sold')
    ax1.set_title('Top 5 Customer Ticket Sold')
    ax2.bar(x_commission, height=y_commission, width=0.3, color='yellow', edgecolor='red')
    ax2.set_xlabel('customer')
    ax2.set_ylabel('commission ($)')
    ax2.set_title('Top 5 Customer Commission Earned')
    fig.legend(loc='center right')
    fig.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('agent_top_customer.html', customer_ticket=customer_ticket,
                                                      customer_commission=customer_commission, plot_url=plot_url)
        
###################### Begin Airline Staff ##################################

#View all upcoming flights (default)
@app.route('/home/staff_view_flight')
def staff_view_flight():
    username = session['username']
    
    cursor = conn.cursor()
    #select the airline that staff works for
    query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(username))
    airline = cursor.fetchone()
    
    #select the incoming flights of this airline
    query = "SELECT * FROM flight WHERE airline_name = \'{}\' AND (departure_time BETWEEN NOW() AND ADDTIME(NOW(), '30 0:0:0'));"
    cursor.execute(query.format(airline[0]))
    flights = cursor.fetchall()
    
    #extract all existing arrival_airport
    query = "SELECT DISTINCT arrival_airport FROM flight"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()
    
    #extract all existing departure_airport
    query = "SELECT DISTINCT departure_airport FROM flight"
    cursor.execute(query)
    departure_airport = cursor.fetchall()
    
    #extract all existing arrival_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT arrival_airport FROM flight)"
    cursor.execute(query)
    arrival_city = cursor.fetchall()
    
    #extract all existing departure_city
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT departure_airport FROM flight)"
    cursor.execute(query)
    departure_city = cursor.fetchall()
    
    #extract all the flight numbers
    query = "SELECT DISTINCT flight_num FROM flight WHERE airline_name = \'{}\';"
    cursor.execute(query.format(airline[0]))
    flight_num = cursor.fetchall()
    cursor.close()
    return render_template('staff_view_flight.html', flights=flights,
                                                     arrival_airport=arrival_airport,
                                                     departure_airport=departure_airport,
                                                     arrival_city=arrival_city,
                                                     departure_city=departure_city,
                                                     airline=airline[0],
                                                     flight_number=flight_num
                                                     )

@app.route('/home/staff_view_flight/staff_search_result', methods=['GET','POST'])
def staff_search_result():
    if request.method == 'POST':
        #grab information based on customer's flight search selection
        airline = request.form['airline']
        departure_city = request.form['departure_city']
        departure_airport = request.form['departure_airport']
        arrival_city = request.form['arrival_city']
        arrival_airport = request.form['arrival_airport']
        starting_date = request.form['starting_date']
        ending_date = request.form['ending_date']
        
        flag1= bool(departure_city != "all")
        flag2 = bool(departure_airport != "all")
        flag3 = bool(arrival_city != "all")
        flag4 = bool(arrival_airport != "all")
        flag5 = bool(starting_date != "" or ending_date != "")
        flag_start = bool(starting_date != "")
        flag_end = bool(ending_date != "")
        if (not flag1 and not flag2 and not flag3 and not flag4 and not flag5):
            error = "At least 1 field should be specified!"
            return render_template('staff_search_result.html', error=error)
        else:
            sub0 = " airline_name = \'{}\' ".format(airline)
            sub1 = " departure_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(departure_city)
            sub2 = " departure_airport = \"{}\" ".format(departure_airport)
            sub3 = " arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city=\'{}\') ".format(arrival_city)
            sub4 = " arrival_airport =\"{}\" ".format(arrival_airport)
            if (flag_start and flag_end):
                sub5 = "( DATE(departure_time) BETWEEN DATE(\'{}\') AND DATE(\'{}\') )".format(starting_date, ending_date)
            elif (flag_start and not flag_end):
                sub5 = "( DATE(departure_time) >= DATE(\'{}\') )".format(starting_date)
            elif (flag_end and not flag_start):
                sub5 = "( DATE(departure_time) <= DATE(\'{}\') )".format(ending_date)
            else:
                sub5 = "empty query"
            # recall that: boolen * string = string if boolen=True, or "" if boolen=False
            merged_sub = list(filter(None,[sub0, flag1*sub1, flag2*sub2, flag3*sub3, flag4*sub4, flag5*sub5]))
            query = "SELECT * FROM flight WHERE " + " AND ".join(merged_sub)
            cursor = conn.cursor()
            cursor.execute(query)
            search = cursor.fetchall()
            cursor.close()
        return render_template('staff_search_result.html', search=search)
    
@app.route('/home/staff_view_flight/staff_view_customer', methods=['GET','POST'])
def staff_view_customer():
    if request.method == 'POST':
        airline = request.form['airline']
        flight_num = request.form['flight_number']
        # select customers of the above flight
        cursor = conn.cursor()
        query = "SELECT c.email, c.name, c.phone_number, c.city, c.state, c.date_of_birth" +\
        " FROM ticket t,  purchases p, customer c WHERE c.email = p.customer_email" +\
        " AND t.ticket_id = p.ticket_id AND t.airline_name = \'{}\' AND t.flight_num = \'{}\';"
        cursor.execute(query.format(airline, flight_num))
        customer = cursor.fetchall()
        if(customer):
            error = None
        else:
            error = 'There is no customer for this flight!'
        return render_template('staff_view_customer.html', customer=customer, error=error)
    
@app.route('/home/staff_create_flight')
def staff_create_flight():
    username = session['username']
    
    cursor = conn.cursor()
    #select the airline that staff works for
    query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(username))
    airline = cursor.fetchone()
    #select the incoming flights of this airline
    query = "SELECT * FROM flight WHERE airline_name = \'{}\' AND (departure_time BETWEEN NOW() AND ADDTIME(NOW(), '30 0:0:0'));"
    cursor.execute(query.format(airline[0]))
    flights = cursor.fetchall()
    #extract all existing arrival_airport
    query = "SELECT DISTINCT airport_name FROM airport"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()
    #extract all existing departure_airport
    query = "SELECT DISTINCT airport_name FROM airport"
    cursor.execute(query)
    departure_airport = cursor.fetchall()
    #extract all existing arrival_city
    query = "SELECT DISTINCT airport_city FROM airport"
    cursor.execute(query)
    arrival_city = cursor.fetchall()
    #extract all existing departure_city
    query = "SELECT DISTINCT airport_city FROM airport"
    cursor.execute(query)
    departure_city = cursor.fetchall()
    #extract all the flight numbers
    query = "SELECT DISTINCT flight_num FROM flight WHERE airline_name = \'{}\';"
    cursor.execute(query.format(airline[0]))
    flight_num = cursor.fetchall()
    #extract all the airplane ids
    query = "SELECT DISTINCT airplane_id FROM airplane WHERE airline_name = \'{}\';"
    cursor.execute(query.format(airline[0]))
    airplane_id = cursor.fetchall()
    cursor.close()
    return render_template('staff_create_flight.html', flights=flights,
                                                     arrival_airport=arrival_airport,
                                                     departure_airport=departure_airport,
                                                     arrival_city=arrival_city,
                                                     departure_city=departure_city,
                                                     airline=airline[0],
                                                     flight_number=flight_num,
                                                     airplane_id=airplane_id
                                                     )

@app.route('/home/StaffCreateAuth', methods=['GET', 'POST'])
def StaffCreateAuth():
    username = session['username']
    identity = session['identity']
    # check illegal actions
    if identity != 'airline_staff':
        flash("Illegal action! Only an airline staff can create a new flight.")
        return redirect(url_for('staff_create_flight'))
    
    airline = request.form['airline']
    flight_num = request.form['flight_num']
    departure_airport = request.form['departure_airport']
    departure_time = request.form['departure_time']
    arrival_airport = request.form['arrival_airport']
    arrival_time = request.form['arrival_time']
    price = request.form['price']
    status = request.form['status']
    airplane_id = request.form['airplane_id']
    
    cursor = conn.cursor()
    query1 = "SELECT * FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\' "
    cursor.execute(query1.format(airline, flight_num))
    data1 = cursor.fetchone()
    #If the previous query returns data, then flight exists
    if(data1):
        flash("This flight already exists!")
        return redirect(url_for('staff_create_flight'))
    #two airports cannot be the same
    if departure_airport == arrival_airport:
        flash("Departure and arrival airport cannot be the same!")
        return redirect(url_for('staff_create_flight'))
    #departure time must be earlier than arrival time
    if departure_time >= arrival_time:
        flash("Departure time must be earlier than arrival time!")
        return redirect(url_for('staff_create_flight'))
    
    ins = "INSERT INTO flight VALUES(\'{}\', \'{}\', \"{}\", \'{}\', \"{}\", \'{}\', \'{}\', \'{}\', \'{}\')"
    cursor.execute(ins.format(airline, flight_num, departure_airport, departure_time,
                              arrival_airport, arrival_time, price, status, airplane_id))
    conn.commit()
    cursor.close()
    
    username = session['username']
    
    cursor = conn.cursor()
    query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(username))
    airline = cursor.fetchone()
    query = "SELECT * FROM flight WHERE airline_name = \'{}\' AND (departure_time BETWEEN NOW() AND ADDTIME(NOW(), '30 0:0:0'));"
    cursor.execute(query.format(airline[0]))
    flights = cursor.fetchall()
    query = "SELECT DISTINCT arrival_airport FROM flight"
    cursor.execute(query)
    arrival_airport = cursor.fetchall()
    query = "SELECT DISTINCT departure_airport FROM flight"
    cursor.execute(query)
    departure_airport = cursor.fetchall()
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT arrival_airport FROM flight)"
    cursor.execute(query)
    arrival_city = cursor.fetchall()
    query = "SELECT DISTINCT airport_city FROM airport WHERE airport_name IN (SELECT departure_airport FROM flight)"
    cursor.execute(query)
    departure_city = cursor.fetchall()
    query = "SELECT DISTINCT flight_num FROM flight WHERE airline_name = \'{}\';"
    cursor.execute(query.format(airline[0]))
    flight_num = cursor.fetchall()
    query = "SELECT DISTINCT airplane_id FROM airplane WHERE airline_name = \'{}\';"
    cursor.execute(query.format(airline[0]))
    airplane_id = cursor.fetchall()
    cursor.close()
    return render_template('staff_create_flight.html', success=True,
                                                       flights=flights,
                                                       arrival_airport=arrival_airport,
                                                       departure_airport=departure_airport,
                                                       arrival_city=arrival_city,
                                                       departure_city=departure_city,
                                                       airline=airline[0],
                                                       flight_number=flight_num,
                                                       airplane_id=airplane_id)
    
@app.route('/home/staff_change_status')
def staff_change_status():
    username = session['username']
    
    cursor = conn.cursor()
    query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(username))
    airline = cursor.fetchone()
    query = "SELECT DISTINCT flight_num FROM flight WHERE airline_name = \'{}\';"
    cursor.execute(query.format(airline[0]))
    flight_num = cursor.fetchall()
    cursor.close()
    return render_template('staff_change_status.html', airline=airline[0],
                                                       flight_num=flight_num)
    
@app.route('/home/StaffConfirmStatus', methods=['GET', 'POST'])
def StaffConfirmStatus():
    username = session['username']
    identity = session['identity']
    # check illegal actions
    if identity != 'airline_staff':
        flash("Illegal action! Only an airline staff can modify a flight.")
        return redirect(url_for('staff_change_status'))
    
    airline = request.form['airline']
    flight_num = request.form['flight_num']
    cursor = conn.cursor()
    query = "SELECT status FROM flight WHERE airline_name = \'{}\' AND flight.flight_num = \'{}\' ;"
    cursor.execute(query.format(airline, flight_num))
    status = cursor.fetchone()
    cursor.close()
    return render_template('staff_change_status.html', confirm=True,
                                                       status=status[0],
                                                       airline=airline,
                                                       flight_num=flight_num)

@app.route('/home/StaffSetFinalStatus', methods=['GET', 'POST'])
def StaffSetFinalStatus():
    username = session['username']
    identity = session['identity']
    # check illegal actions
    if identity != 'airline_staff':
        flash("Illegal action! Only an airline staff can modify a flight.")
        return redirect(url_for('staff_change_status'))
    
    airline = request.form['airline']
    flight_num = request.form['flight_num']
    new_status = request.form['selected_status']
    cursor = conn.cursor()
    query = "UPDATE flight SET status = \'{}\' WHERE flight.airline_name = \'{}\' AND flight.flight_num = \'{}\' ;"
    cursor.execute(query.format(new_status, airline, flight_num))
    conn.commit()
    cursor.close()
    flash('You have successfully updated flight status!')
    return redirect(url_for('staff_change_status'))

@app.route('/home/staff_add_airplane')
def staff_add_airplane():
    username = session['username']
    cursor = conn.cursor()
    query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(username))
    airline = cursor.fetchone()
    cursor.close()
    return render_template('staff_add_airplane.html', airline=airline[0])

@app.route('/home/StaffAddPlaneAuth', methods=['GET', 'POST'])
def StaffAddPlaneAuth():
    username = session['username']
    identity = session['identity']
    # check illegal actions
    if identity != 'airline_staff':
        flash("Illegal action! Only an airline staff can modify a flight.")
        return redirect(url_for('staff_add_airplane'))
    
    airline = request.form['airline']
    seats = request.form['seats']
    #assign an airplane_id to the added plane
    cursor = conn.cursor()
    
    query = "SELECT MAX(airplane_id) FROM airplane WHERE airline_name = \'{}\'; "
    cursor.execute(query.format(airline))
    old_id = cursor.fetchone()
    cursor.close()
    if not old_id[0]: # no plane exists yet
        new_id = 1
    else:
        new_id = int(old_id[0]) + 1
    
    cursor = conn.cursor()
    query = "INSERT INTO airplane VALUES(\'{}\', \'{}\', \'{}\');"
    cursor.execute(query.format(airline, new_id, seats))
    conn.commit()
    cursor.close()
    
    #get all the existing airplanes
    cursor = conn.cursor()
    query = "SELECT * FROM airplane WHERE airline_name = \'{}\'; "
    cursor.execute(query.format(airline))
    planes = cursor.fetchall()
    cursor.close()
    return render_template('staff_add_airplane_confirmation.html', airplane=planes)

@app.route('/home/staff_add_airport')
def staff_add_airport():
    return render_template('staff_add_airport.html')

@app.route('/home/StaffAddAirportAuth', methods=['GET', 'POST'])
def StaffAddAirportAuth():
    username = session['username']
    identity = session['identity']
    # check illegal actions
    if identity != 'airline_staff':
        flash("Illegal action! Only an airline staff can modify a flight.")
        return redirect(url_for('staff_add_airport'))
    
    airport = request.form['airport_name']
    city = request.form['city']
    #check duplicated airport name
    cursor = conn.cursor()
    query = "SELECT EXISTS(SELECT * FROM airport WHERE airport_name = \"{}\"); "
    cursor.execute(query.format(airport))
    flag = cursor.fetchone()
    if flag[0] == 1: # duplicated name exists
        flash("Do not enter a duplicated airport name!")
        return redirect(url_for('staff_add_airport'))
    cursor.close()
    cursor = conn.cursor()
    query = "INSERT INTO airport VALUES(\"{}\", \'{}\');"
    cursor.execute(query.format(airport, city))
    conn.commit()
    cursor.close()
    return render_template('staff_add_airport.html', success='success')

@app.route('/home/staff_view_agent')
def staff_view_agent():
    username = session['username']
    
    #find top agents in past month based on tickets sold
    query = "SELECT b.email, b.booking_agent_id, COUNT(p.ticket_id) " +\
            "FROM booking_agent b, purchases p " +\
            "WHERE p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -1 MONTH) " +\
            "AND p.booking_agent_id = b.booking_agent_id GROUP BY b.email, b.booking_agent_id " +\
            "ORDER BY COUNT(p.ticket_id) DESC; "
    cursor = conn.cursor()
    cursor.execute(query)
    agent = []
    #scan the results to fetch <= top 5 customers if exist
    agt = cursor.fetchone()
    count = 1
    while agt and count <= 5:
        agent.append(list(agt))
        agt = cursor.fetchone()
        count += 1
    cursor.close()
    agent_ticket_month = tuple(agent)
    
    #find top agents in past year based on tickets sold
    query = "SELECT b.email, b.booking_agent_id, COUNT(p.ticket_id) " +\
            "FROM booking_agent b, purchases p " +\
            "WHERE p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -12 MONTH) " +\
            "AND p.booking_agent_id = b.booking_agent_id GROUP BY b.email, b.booking_agent_id " +\
            "ORDER BY COUNT(p.ticket_id) DESC; "
    cursor = conn.cursor()
    cursor.execute(query)
    agent = []
    #scan the results to fetch <= top 5 customers if exist
    agt = cursor.fetchone()
    count = 1
    while agt and count <= 5:
        agent.append(list(agt))
        agt = cursor.fetchone()
        count += 1
    cursor.close()
    agent_ticket_year = tuple(agent)
    
    #find top agents in past year based on commission earned
    query = "SELECT b.email, b.booking_agent_id, 0.1*SUM(f.price) " +\
            "FROM booking_agent b, purchases p, ticket t, flight f " +\
            "WHERE p.purchase_date >= ADDDATE(DATE(NOW()), INTERVAL -12 MONTH) " +\
            "AND p.booking_agent_id = b.booking_agent_id AND " +\
            "f.flight_num = t.flight_num AND f.airline_name = t.airline_name " +\
            "AND t.ticket_id = p.ticket_id GROUP BY b.email, b.booking_agent_id " +\
            "ORDER BY SUM(f.price) DESC; "
    cursor = conn.cursor()
    cursor.execute(query)
    agent = []
    #scan the results to fetch <= top 5 customers if exist
    agt = cursor.fetchone()
    count = 1
    while agt and count <= 5:
        agent.append(list(agt))
        agt = cursor.fetchone()
        count += 1
    cursor.close()
    agent_commission = tuple(agent)
    
    return render_template('staff_view_agent.html', agent_ticket_month=agent_ticket_month,
                                                    agent_ticket_year=agent_ticket_year,
                                                    agent_commission=agent_commission)

@app.route('/home/staff_view_freq_customer')
def staff_view_freq_customer():
    username = session['username']
    
    cursor = conn.cursor()
    #select the airline that staff works for
    query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(username))
    airline = cursor.fetchone()
    
    create_view = "CREATE VIEW customer_frequency AS( " + \
                "SELECT p.customer_email AS email, COUNT(p.ticket_id) AS frequency " +\
                "FROM purchases p, ticket t " +\
                "WHERE t.airline_name = \'{}\' AND t.ticket_id = p.ticket_id "+\
                "GROUP BY p.customer_email); "
    cursor.execute(create_view.format(airline[0]))
    conn.commit()
    
    create_view = "CREATE VIEW max_frequency AS( SELECT MAX(frequency) as max_f FROM customer_frequency); "
    cursor.execute(create_view)
    conn.commit()
            
    query = "SELECT c.email, name, city, state, phone_number, date_of_birth " +\
            "FROM customer c, customer_frequency f, max_frequency m " +\
            "WHERE c.email = f.email AND f.frequency = m.max_f; "
    cursor.execute(query)
    most_freq_customer = cursor.fetchall()
            
    drop_view = "DROP VIEW customer_frequency;"
    cursor.execute(drop_view)
    conn.commit()
    drop_view = "DROP VIEW max_frequency;"
    cursor.execute(drop_view)
    conn.commit()
    
    query = "SELECT email FROM customer"
    cursor.execute(query)
    email = cursor.fetchall()
    cursor.close()
    return render_template('staff_view_freq_customer.html', most_freq_customer=most_freq_customer,
                                                            email=email)
    
@app.route('/home/staff_view_freq_customer/StaffViewCustomerFlight', methods=['GET', 'POST'])
def StaffViewCustomerFlight():
    if request.method == 'POST':
        username = session['username']
        identity = session['identity']
        # check illegal actions
        if identity != 'airline_staff':
            flash("Illegal action! Only an airline staff can modify a flight.")
            return redirect(url_for('staff_view_freq_customer'))
        
        cursor = conn.cursor()
        #select the airline that staff works for
        query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
        cursor.execute(query.format(username))
        airline = cursor.fetchone()
        cursor.close()
        email = request.form['email']
        cursor = conn.cursor()
        query = "SELECT f.airline_name, f.flight_num, f.departure_airport, f.departure_time, " +\
                "f.arrival_airport, f.arrival_time, f.price, f.status, f.airplane_id " +\
                "FROM flight f, purchases p, ticket t " +\
                "WHERE p.customer_email = \'{}\' AND p.ticket_id = t.ticket_id " +\
                "AND t.airline_name = f.airline_name AND t.flight_num = f.flight_num AND f.airline_name = \'{}\' ;"
        cursor.execute(query.format(email, airline[0]))
        flight = cursor.fetchall()
        cursor.close()
        return render_template('staff_view_customer_flight_result.html', flight=flight)
    
@app.route('/home/staff_top_destination')
def staff_top_destination():
    username = session['username']
    
    cursor = conn.cursor()
    #select the airline that staff works for
    query = "SELECT airline_name FROM airline_staff WHERE username = \'{}\'"
    cursor.execute(query.format(username))
    airline = cursor.fetchone()
    cursor.close()
    #query for top destinations in the past 3 months
    month_query = "SELECT f.arrival_airport, a.airport_city " +\
                  "FROM purchases p, ticket t, flight f, airport a " +\
                  "WHERE p.ticket_id = t.ticket_id AND t.airline_name = f.airline_name " +\
                  "AND t.flight_num = f.flight_num AND f.airline_name = \'{}\' AND " +\
                  "(f.arrival_time BETWEEN ADDDATE(NOW(), INTERVAL -3 MONTH) AND NOW()) " +\
                  "AND a.airport_name = f.arrival_airport " +\
                  "GROUP BY f.arrival_airport, a.airport_city ORDER BY COUNT(p.customer_email) DESC;"
    cursor = conn.cursor()
    cursor.execute(month_query.format(airline[0]))
    destination = []
    #scan the results to fetch <= top 3 flights if exist
    dest = cursor.fetchone()
    count = 1
    while dest and count <= 3:
        destination.append(list(dest))
        dest = cursor.fetchone()
        count += 1 
    cursor.close()
    destination_month = tuple(destination)
    
    #query for top destinations in the past year
    year_query = "SELECT f.arrival_airport, a.airport_city " +\
                 "FROM purchases p, ticket t, flight f, airport a " +\
                 "WHERE p.ticket_id = t.ticket_id AND t.airline_name = f.airline_name " +\
                 "AND t.flight_num = f.flight_num AND f.airline_name = \'{}\' AND " +\
                 "(f.arrival_time BETWEEN ADDDATE(NOW(), INTERVAL -12 MONTH) AND NOW()) " +\
                 "AND a.airport_name = f.arrival_airport " +\
                 "GROUP BY f.arrival_airport, a.airport_city ORDER BY COUNT(p.customer_email) DESC;"
    cursor = conn.cursor()
    cursor.execute(year_query.format(airline[0]))
    destination = []
    #scan the results to fetch <= top 3 flights if exist
    dest = cursor.fetchone()
    count = 1
    while dest and count <= 3:
        destination.append(list(dest))
        dest = cursor.fetchone()
        count += 1
    cursor.close()
    destination_year = tuple(destination)
    
    return render_template('staff_top_destination.html', destination_month=destination_month,
                                                         destination_year=destination_year)
    
@app.route('/home/staff_revenue_comparison')
def staff_revenue_comparison():
	username = session['username']
	airline_query = "SELECT airline_name FROM airline_staff WHERE username=\'{}\'".format(username)
	
	cursor = conn.cursor()
	cursor.execute(airline_query)
	airline = cursor.fetchone()[0] # retrieve which airline company does this staff work for
	cursor.close()
	
	# last month non_agent revenue
	non_agent_last_month_query = "SELECT SUM(price) FROM flight NATURAL JOIN purchases NATURAL JOIN ticket WHERE airline_name=\'{}\' AND booking_agent_id is NULL AND (purchase_date BETWEEN DATE_SUB(DATE(NOW()), interval 30 DAY) AND DATE(NOW()) )".format(airline)
	cursor = conn.cursor()
	cursor.execute(non_agent_last_month_query)
	non_agent_last_month = cursor.fetchone()
	cursor.close()
	if not non_agent_last_month[0]:
		non_agent_last_month = 0
	else:
		non_agent_last_month = int(non_agent_last_month[0])
	
	# last month agent revenue
	agent_last_month_query = "SELECT SUM(price) FROM flight NATURAL JOIN purchases NATURAL JOIN ticket WHERE airline_name=\'{}\' AND booking_agent_id is NOT NULL AND (purchase_date BETWEEN DATE_SUB(DATE(NOW()), interval 30 DAY) AND DATE(NOW()) )".format(airline)
	cursor = conn.cursor()
	cursor.execute(agent_last_month_query)
	agent_last_month = cursor.fetchone()
	cursor.close()
	if not agent_last_month[0]:
		agent_last_month = 0
	else:
		agent_last_month = int(agent_last_month[0])
		
	# last year non_agent revenue
	non_agent_last_year_query = "SELECT SUM(price) FROM flight NATURAL JOIN purchases NATURAL JOIN ticket WHERE airline_name=\'{}\' AND booking_agent_id is NULL AND (purchase_date BETWEEN DATE_SUB(DATE(NOW()), interval 365 DAY) AND DATE(NOW()) )".format(airline)
	cursor = conn.cursor()
	cursor.execute(non_agent_last_year_query)
	non_agent_last_year = cursor.fetchone()
	cursor.close()
	if not non_agent_last_year[0]:
		non_agent_last_year = 0
	else:
		non_agent_last_year = int(non_agent_last_year[0])
	
	# last year agent revenue
	agent_last_year_query = "SELECT SUM(price) FROM flight NATURAL JOIN purchases NATURAL JOIN ticket WHERE airline_name=\'{}\' AND booking_agent_id is NOT NULL AND (purchase_date BETWEEN DATE_SUB(DATE(NOW()), interval 365 DAY) AND DATE(NOW()) )".format(airline)
	cursor = conn.cursor()
	cursor.execute(agent_last_year_query)
	agent_last_year = cursor.fetchone()
	cursor.close()
	if not agent_last_year[0]:
		agent_last_year = 0
	else:
		agent_last_year = int(agent_last_year[0])
	
	# retrieve the exact date of last month and last year
	# today
	today_date_query = "SELECT DATE(NOW())"
	cursor = conn.cursor()
	cursor.execute(today_date_query)
	today_date = cursor.fetchone()[0]
	cursor.close()
	
	# last month
	last_month_date_query = "SELECT DATE_SUB(DATE(NOW()), interval 30 DAY)"
	cursor = conn.cursor()
	cursor.execute(last_month_date_query)
	last_month_date = cursor.fetchone()[0]
	cursor.close()
	
	# last month
	last_year_date_query = "SELECT DATE_SUB(DATE(NOW()), interval 365 DAY)"
	cursor = conn.cursor()
	cursor.execute(last_year_date_query)
	last_year_date = cursor.fetchone()[0]
	cursor.close()
	
	# generate two pie chart within one subplot pic
	img = BytesIO()
	fig, (ax1, ax2) = plt.subplots(2, figsize=(10,10))
	fig.suptitle('Direct v.s. Indirect Revenue earned')
	ax1.set_title('last month')
	ax1.pie([non_agent_last_month,agent_last_month], labels=['Direct','Indirect'], autopct=make_autopct([non_agent_last_month,agent_last_month]))
	ax2.set_title('last year')
	ax2.pie([non_agent_last_year,agent_last_year], labels=['Direct','Indirect'], autopct=make_autopct([non_agent_last_year,agent_last_year]))
	fig.legend(loc='center right')
	fig.savefig(img, format='png')
	img.seek(0)
	plot_url = base64.b64encode(img.getvalue()).decode('utf8')
	
	return render_template('staff_revenue_comparison.html', airline=airline, today_date=today_date, last_month_date = last_month_date, last_year_date=last_year_date, non_agent_last_month=non_agent_last_month, agent_last_month=agent_last_month, non_agent_last_year=non_agent_last_year, agent_last_year=agent_last_year, plot_url=plot_url)
	
@app.route('/home/staff_view_report', methods=['GET', 'POST'])
def staff_view_report():
	# extract which airline does this staff work for
	username = session['username']
	airline_query = "SELECT airline_name FROM airline_staff WHERE username=\'{}\'".format(username)
	cursor = conn.cursor()
	cursor.execute(airline_query)
	airline = cursor.fetchone()[0]
	cursor.close()
	
	# retrieve the exact date of last month and last year
	# today
	today_date_query = "SELECT DATE(NOW())"
	cursor = conn.cursor()
	cursor.execute(today_date_query)
	today_date = cursor.fetchone()[0]
	cursor.close()
	
	# last month
	last_month_date_query = "SELECT DATE_SUB(DATE(NOW()), interval 30 DAY)"
	cursor = conn.cursor()
	cursor.execute(last_month_date_query)
	last_month_date = cursor.fetchone()[0]
	cursor.close()
	
	# last month
	last_year_date_query = "SELECT DATE_SUB(DATE(NOW()), interval 365 DAY)"
	cursor = conn.cursor()
	cursor.execute(last_year_date_query)
	last_year_date = cursor.fetchone()[0]
	cursor.close()
	
	# last month ticket sold
	last_month_ticket_query = "SELECT COUNT(*) FROM purchases NATURAL JOIN flight NATURAL JOIN ticket WHERE airline_name=\'{}\' AND DATE(purchase_date) BETWEEN \'{}\' AND \'{}\'".format(airline, last_month_date, today_date)
	cursor = conn.cursor()
	cursor.execute(last_month_ticket_query)
	last_month_ticket = cursor.fetchone()
	if not last_month_ticket:
		last_month_ticket = 0
	else:
		last_month_ticket = int(last_month_ticket[0])
	cursor.close()
	
	# last year ticket sold
	last_year_ticket_query = "SELECT COUNT(*) FROM purchases NATURAL JOIN flight NATURAL JOIN ticket WHERE airline_name=\'{}\' AND DATE(purchase_date) BETWEEN \'{}\' AND \'{}\'".format(airline, last_year_date, today_date)
	cursor = conn.cursor()
	cursor.execute(last_year_ticket_query)
	last_year_ticket = cursor.fetchone()
	if not last_year_ticket:
		last_year_ticket = 0
	else:
		last_year_ticket = int(last_year_ticket[0])
	cursor.close()
	
	# generate the default past year ticket sales report bar chart
	month_query = "SELECT YEAR(date_sub(DATE(NOW()), interval {} month)) as year, MONTH(date_sub(DATE(NOW()), interval {} month)) as month, COUNT(*) FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE airline_name=\'{}\' AND YEAR(purchase_date)=YEAR(date_sub(DATE(NOW()), interval {} month)) AND MONTH(purchase_date) = MONTH(date_sub(DATE(NOW()), interval {} month))"
	month_query_list = [month_query.format("0","0",airline, "0", "0"),month_query.format("1","1",airline, "1", "1"),month_query.format("2","2",airline, "2", "2"),month_query.format("3","3",airline, "3", "3"),month_query.format("4","4",airline, "4", "4"),month_query.format("5","5",airline, "5", "5"),month_query.format("6","6",airline, "6", "6"),month_query.format("7","7",airline, "7", "7"),month_query.format("8","8",airline, "8", "8"),month_query.format("9","9",airline, "9", "9"),month_query.format("10","10",airline, "10", "10"),month_query.format("11","11",airline, "11", "11"),month_query.format("12","12",airline, "12", "12")]
	# query list to generate the past year's ticket sold counting
	month_index = []
	month_ticket = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	cursor = conn.cursor()
	for i,query in enumerate(month_query_list):
		cursor.execute(query)
		ticket = cursor.fetchone()
		if ticket[2]:
			month_ticket[i] = int(ticket[2])
		month_index.append(str(ticket[0])+'-'+str(ticket[1]))
	cursor.close()
    #generate the bar chart plot
	month_index.reverse()
	month_ticket.reverse()
	img = BytesIO()
	plt.clf()
	ax = plt.gca()
	ax.tick_params(axis = 'both', which = 'major', labelsize = 6)
	plt.bar(month_index, height=month_ticket, width= 0.5)
	plt.xlabel("month")
	plt.ylabel("ticket sold")
	plt.title("Ticket Sales Report-Last Year")
	img.seek(0)
	plt.savefig(img, format='png')
	plot_url = base64.b64encode(img.getvalue()).decode('utf8')

	return render_template("staff_view_report.html", airline=airline, today_date=today_date, last_month_date=last_month_date, last_year_date=last_year_date, last_month_ticket=last_month_ticket, last_year_ticket=last_year_ticket, plot_url=plot_url)
	
@app.route('/home/staff_customize_view_report', methods=['GET', 'POST'])
def staff_customize_view_report():
	username = session['username']
	start = request.form['start_month']
	end = request.form['end_month']
	airline_query = "SELECT airline_name FROM airline_staff WHERE username=\'{}\'".format(username)
	cursor = conn.cursor()
	cursor.execute(airline_query)
	airline = cursor.fetchone()[0]
	cursor.close()
	if ((not start) or (not end)): # both start/end month for ticket sale search must be specified
		error = "Both starting month and ending month must be specified for customized ticket sales report!"
		return render_template('staff_customize_view_report_failure.html', error = error)
	elif start > end:
		error = "starting month must be no later than ending month!"
		return render_template('staff_customize_view_report_failure.html', error = error)
	else:
		start_year, start_month = start[:4], start[-2:]
		end_year, end_month = end[:4], end[-2:]
		old_start, old_end = start, end
		# You have to append the "Day" 'xxxx-xx-01' to make this function works properly,
		# otherwise, the TIMESTAMPDIFF function returns None
		start, end = start+'-01', end+'-01'
		cursor = conn.cursor()
		month_gap_query = "SELECT TIMESTAMPDIFF(MONTH, \'{}\', \'{}\')".format(start, end)
		cursor.execute(month_gap_query)
		month_gap = cursor.fetchone()[0]
		cursor.close()
		month_query = "SELECT YEAR(date_sub(DATE(\'{}\'), interval {} month)) as year, MONTH(date_sub(DATE(\'{}\'), interval {} month)) as month, COUNT(*) FROM ticket NATURAL JOIN purchases NATURAL JOIN flight WHERE airline_name=\'{}\' AND YEAR(purchase_date)=YEAR(date_sub(DATE(\'{}\'), interval {} month)) AND MONTH(purchase_date) = MONTH(date_sub(DATE(\'{}\'), interval {} month))"
		month_query_list = [month_query.format(end, i, end, i, airline, end, i, end, i) for i in range(month_gap+1)] # create the query for each month's ticket sale
		month_index = []
		month_ticket = [0] * (month_gap + 1)
		cursor = conn.cursor()
		for i, query in  enumerate(month_query_list):
			cursor.execute(query)
			ticket = cursor.fetchone()
			if ticket[2]:
				month_ticket[i] = int(ticket[2])
			month_index.append(str(ticket[0])+'-'+str(ticket[1]))
		cursor.close()
		month_index.reverse()
		month_ticket.reverse()
		# open a "deceiving" ByteIO thread to generate the return plot
		img = BytesIO()
		plt.clf()
		ax = plt.gca()
		ax.tick_params(axis = 'both', which = 'major', labelsize = 6)
		plt.bar(month_index, height=month_ticket, width= 0.5)
		plt.xlabel("month")
		plt.ylabel("ticket sold")
		plt.title("Ticket Sales Report-Customized")
		img.seek(0)
		plt.savefig(img, format='png')
		plot_url = base64.b64encode(img.getvalue()).decode('utf8')
		
		return render_template('staff_customize_view_report.html', start_year=start_year, start_month=start_month, end_year=end_year, end_month=end_month, airline=airline, plot_url=plot_url)
		
###################### End Airline Staff ##################################

#logout from home
@app.route('/logout')
def logout():
    session.pop('username')
    session.pop('identity')
    return redirect('/')

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
