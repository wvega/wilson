<?php

// Safe Search and Replace on Database with Serialized Data v1.0.1

// This script is to solve the problem of doing database search and replace
// when developers have only gone and used the non-relational concept of
// serializing PHP arrays into single database columns.  It will search for all
// matching data on the database and change it, even if it's within a serialized
// PHP array.

// The big problem with serialised arrays is that if you do a normal DB
// style search and replace the lengths get mucked up.  This search deals with
// the problem by unserializing and reserializing the entire contents of the
// database you're working on.  It then carries out a search and replace on the
// data it finds, and dumps it back to the database.  So far it appears to work
// very well.  It was coded for our WordPress work where we often have to move
// large databases across servers, but I designed it to work with any database.
// Biggest worry for you is that you may not want to do a search and replace on
// every damn table - well, if you want, simply add some exclusions in the table
// loop and you'll be fine.  If you don't know how, you possibly shouldn't be
// using this script anyway.

// To use, simply configure the settings below and off you go.  I wouldn't
// expect the script to take more than a few seconds on most machines.

// BIG WARNING!  Take a backup first, and carefully test the results of this code.
// If you don't, and you vape your data then you only have yourself to blame.
// Seriously.  And if you're English is bad and you don't fully understand the
// instructions then STOP.  Right there.  Yes.  Before you do any damage.

// USE OF THIS SCRIPT IS ENTIRELY AT YOUR OWN RISK.  I/We accept no liability from its use.

// Written 20090525 by David Coveney of Interconnect IT Ltd (UK)
// http://www.davesgonemental.com or http://www.interconnectit.com or
// http://spectacu.la and released under the WTFPL
// ie, do what ever you want with the code, and I take no responsibility for it OK?
// If you don't wish to take responsibility, hire me through Interconnect IT Ltd
// on +44 (0)151 331 5140 and we will do the work for you, but at a cost, minimum 1hr
// To view the WTFPL go to http://sam.zoy.org/wtfpl/ (WARNING: it's a little rude, if you're sensitive)

// Version 1.0.1 - styling and form added by James R Whitehead.
// Version 1.1   - converted to a PHP Shell Script by Willington Vega

// Credits:  moz667 at gmail dot com for his recursive_array_replace posted at
//             uk.php.net which saved me a little time - a perfect sample for me
//           and seems to work in all cases.

// TODO: Only work on Wordpress Tables (use table prefix)

// Usage:
// php searchandreplacedb.php pattern replacement host username password database [report]


// Utility functions

global $REPORT;



function recursive_array_replace($find, $replace, &$data) {
    if (is_array($data)) {
        foreach ($data as $key => $value) {
            if (is_array($value)) {
                recursive_array_replace($find, $replace, $data[$key]);
            } else {
                // have to check if it's string to ensure no switching to string for booleans/numbers/nulls - don't need any nasty conversions
                if (is_string($value)) $data[$key] = str_replace($find, $replace, $value);
            }
        }
    } else {
        if (is_string($data)) $data = str_replace($find, $replace, $data);
    }
}

function report($message) {
    global $REPORT;
    if ($REPORT) {
        echo $message;
    }
}



$REPORT = isset($argv[7]) ? (bool) $argv[7] : false;

// Let's start. Grab command line arguments and create a connection

$pattern = $argv[1];
$replacement = $argv[2];
$host = $argv[3];
$usr = $argv[4];
$pwd = $argv[5];
$db = $argv[6];

$cid = mysql_connect($host,$usr,$pwd);
if (!$cid) {
    die("Connecting to DB Error: " . mysql_error() . "\n");
}

mysql_select_db($db);

// First, get a list of tables

$SQL = "SHOW TABLES";
$tables_list = mysql_query($SQL, $cid);

if (!$tables_list) {
    die("ERROR: " . mysql_error() . "\n$SQL\n");
}

report("\nSearch & Replace\n");
report("Replace '$pattern' with '$replacement'\n\n");

// Counters used later to report what was done
$count_tables_checked = 0;
$count_items_checked = 0;
$count_items_changed = 0;
$count_updates_run = 0;

// Loop through the tables

while ($table_rows = mysql_fetch_array($tables_list)) {

    $count_tables_checked++;
    $table = $table_rows['Tables_in_'.$db];

    report("Checking table: ".$table."\n");  // we have tables!
    
    $SQL = "DESCRIBE ".$table ;    // fetch the table description so we know what to do with it
    $fields_list = mysql_query($SQL, $cid);

    // Make a simple array of field column names

    $index_fields = "";  // reset fields for each table.
    $column_name = "";
    $table_index = "";
    $i = 0;

    while ($field_rows = mysql_fetch_array($fields_list)) {
        $column_name[$i] = $field_rows['Field'];
        if ($field_rows['Key'] == 'PRI') {
            $table_index[$i] = true ;
        }
        $i++;
    }

    // Now let's get the data and do search and replaces on it...

    $SQL = "SELECT * FROM ".$table;     // fetch the table contents
    $data = mysql_query($SQL, $cid);

    if (!$data) {
        report("\tERROR: " . mysql_error() . "\n$SQL\n");
    }

    while ($row = mysql_fetch_array($data)) {
        
        // Initialise the UPDATE string we're going to build, and we don't do an update for each damn column...
        $need_to_update = false;
        $UPDATE_SQL = 'UPDATE '.$table. ' SET ';
        $WHERE_SQL = ' WHERE ';

        $j = -1;

        foreach ($column_name as $current_column) {
            $j++; $count_items_checked++;

            $data_to_fix = $row[$current_column];
            $edited_data = $data_to_fix;            // set the same now - if they're different later we know we need to update

            // added @ operator to suppres E_NOTICE
            $unserialized = @unserialize($data_to_fix);  // unserialise - if false returned we don't try to process it as serialised

            if ($unserialized) {
                recursive_array_replace($pattern, $replacement, $unserialized);
                $edited_data = serialize($unserialized);
            } else if (is_string($data_to_fix)) {
                $edited_data = str_replace($pattern,$replacement,$data_to_fix) ;
            }

            if ($data_to_fix != $edited_data) {   // If they're not the same, we need to add them to the update string
                $count_items_changed++;
                if ($need_to_update != false) {
                    $UPDATE_SQL = $UPDATE_SQL.',';  // if this isn't our first time here, add a comma
                }
                $UPDATE_SQL = $UPDATE_SQL.' '.$current_column.' = "'.mysql_real_escape_string($edited_data).'"' ;
                $need_to_update = true; // only set if we need to update - avoids wasted UPDATE statements
            }

            if (isset($table_index[$j]) && $table_index[$j]) {
                $WHERE_SQL = $WHERE_SQL.$current_column.' = "'.$row[$current_column].'" AND ';
            }
        }

        if ($need_to_update) {
            $count_updates_run++;
            // strip off the excess AND - the easiest way to code this without extra flags, etc.
            $UPDATE_SQL = $UPDATE_SQL.substr($WHERE_SQL,0,-4);
            $result = mysql_query($UPDATE_SQL,$cid);

            if (!$result) {
                report("\tERROR: " . mysql_error() . "\n$UPDATE_SQL\n");
            } else {
                //report("\t$UPDATE_SQL.\n");
            }
        }
    }
}

// Report

report("\n================================================================================\n");
report("Tables Checked: $count_tables_checked.\tItems Checked: $count_items_checked.\tItems Changed: $count_items_changed.\n\n");

mysql_close($cid);