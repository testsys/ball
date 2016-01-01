#!/bin/bash

set +e

init="false"
if [ "$1" == "--init" ] ; then
  init="true"
  shift
fi

event_id="$1"
event_date="$2"

[ -z "$event_id" ] && exit 1
[ -z "$event_date" ] && exit 1

wget -O import.dat https://acm.math.spbu.ru/cgi-bin/view.pl/n${event_date}.dat -o /dev/null

if [ "$init" == "true" ] ; then
  #exit
  x=$(echo "select id from events where id=$event_id" | ../mysql | tail -1)
  if [ -z "$x" ] ; then
    echo "insert into events(id) values($event_id)" | ../mysql
  fi
  event_name="$(grep -a '@contest' import.dat | sed -E 's/@contest //' | sed -e 's/"//g' | sed -E 's/.$//')"
  echo "update events set name='$event_name' where id=$event_id" | ../mysql

  grep -a -E '^@p ' import.dat | sed -E 's/@p //' | sed -E 's/^([A-Za-z]*),/\1 /' | sed -E 's/,[0-9]*,[0-9]*.$//' |
  while read pn p ; do
    pp=$(echo $p | sed -E "s/'/\"/g")
    echo "insert into problems(letter, name, event_id) values('$pn', '$pp', $event_id)" | ../mysql
  done
fi

OKS=$(grep -a -E '^@s ' import.dat | grep -a -E ',OK' | awk '{print $2;}')
for ok in $OKS ; do
  team_name=$(echo $ok | sed -E 's/,/ /g' | awk '{print $1;}')
  problem_letter=$(echo $ok | sed -E 's/,/ /g' | awk '{print $2;}')
  problem_id=$(echo "select id from problems where event_id=$event_id and letter='$problem_letter'" | ../mysql | tail -1)
  team_id=$(echo "select id from teams where event_id=$event_id and name='$team_name'" | ../mysql | tail -1)
  if [ -z "$team_id" ] ; then
    echo "insert into teams(event_id, name) values($event_id, '$team_name')" | ../mysql
    team_id=$(echo "select id from teams where event_id=$event_id and name='$team_name'" | ../mysql | tail -1)
  fi
  date=$(date +%s)
  balloon_id=$(echo "select id from balloons where event_id=$event_id and problem_id=$problem_id and team_id=$team_id" | ../mysql | tail -1)
  echo "$team_name $problem_letter $problem_id $team_id $balloon_id"
  if [ -z "$balloon_id" ] ; then
    echo "insert into balloons(event_id, problem_id, team_id, state, time_created) values($event_id, $problem_id, $team_id, 0, $date)" | ../mysql
  fi
done
