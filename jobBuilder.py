import sys

from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async
from shutil import copyfile

import config
import jenkins
import strings
import os

reload(sys)
sys.setdefaultencoding('utf-8')

# jenkins server instance
server = None
# record jenkins branch list
branches = []


def init(url, username, token):
    global server
    server = jenkins.Jenkins(url, username, token)
    user = server.get_whoami()
    print '[Jenkins bot] loggined url: %s, user: %s' % (url, user['id'])
    global jobName 
    jobName = config.jenkins_job
    
def refresh():
    init()

def isAdmin(bot, update):
    username = update.message.from_user.username
    if username in config.admin_users:
        return True
    else:
        s = 'Deny User: ' + ' [' + username + ']\n'+strings.NO_ACCESS +""
        bot.sendMessage(update.message.chat_id, text=s)
        return False

def isAllowedUsers(bot, update):
    username = update.message.from_user.username
    if username in config.allowed_users:
        return True
    else:
        s = 'Invalid User: ' + ' [' + username + '] \n' + strings.NO_ACCESS
        bot.sendMessage(update.message.chat_id, text=s)
        return False

def isUserExist(username):
    if username in config.allowed_users:
        print username + "exist"
        return True
    else:
	print username + "not"
        return False

@run_async
def addUser(bot,update,args):
    if not isAdmin(bot, update):
        return

    if args:
        rtext = args[0]
    else:
        rtext = ''
    rtext=(rtext[1:])
    print rtext
    if isUserExist(rtext):
        bot.sendMessage(update.message.chat_id, text=args[0]+" " +strings.USER_EXIST)
        return
    else:
   	input = sys.stdin
        output = sys.stdout
    	input = open('/data/script/jobbuilder/config1.py')
        output= open('/data/script/jobbuilder/config.py','w')
	stext="allowed_users = [\'alexfman\',"
    	rtext= "allowed_users = [\'alexfman\','"+ rtext +"',"
    	print rtext

     	for s in input.xreadlines():
       		output.write(s.replace(stext, rtext))
    	output.close()
    	input.close()
        copyfile('/data/script/jobbuilder/config.py','/data/script/jobbuilder/config1.py')
    	bot.sendMessage(update.message.chat_id, text=args[0]+" " +strings.ADD_ACCESS)
        myCmd = 'pkill -f /data/script/jobbuilder/jobBuilder.py'
        os.system(myCmd)
        return

@run_async
def rmUser(bot,update,args):
    if not isAdmin(bot, update):
        return
    if args:
        stext = args[0]
    else:
        stext = ''
    stext=(stext[1:])
    if not isUserExist(stext):
        bot.sendMessage(update.message.chat_id, text=args[0]+" " +strings.USER_DOES_NOT_EXIST)
        return
    else:
	input = sys.stdin
    	output = sys.stdout
    	input = open('/data/script/jobbuilder/config1.py')
  	output= open('/data/script/jobbuilder/config.py','w')
	stext="'"+stext+"',"
    	rtext= ""
    	for s in input.xreadlines(  ):
       		output.write(s.replace(stext, rtext))
    	output.close()
    	input.close()
    	copyfile('/data/script/jobbuilder/config.py','/data/script/jobbuilder/config1.py')
    	bot.sendMessage(update.message.chat_id, text=args[0]+" "+strings.REMOVE_ACCESS)
        myCmd = 'pkill -f /data/script/jobbuilder/jobBuilder.py'
	os.system(myCmd)
    	return


@run_async
def startBuildJob(bot, update):
    if not isAllowedUsers(bot, update):
        bot.sendMessage(update.message.chat_id, text=strings.NO_ACCESS)
        return

    if not isAlreadyBuilding(jobName):
        print 'building ' + jobName
        server.build_job(jobName)
        s = 'start building ' + jobName 
        print s
        bot.sendMessage(update.message.chat_id, text=s)
        return
    else:
        s = jobName + string.ALREADY_BUILD
        print s
        bot.sendMessage(update.message.chat_id, text=s)
        return


def isAlreadyBuilding(jobName):
    running_builds = server.get_running_builds()
    for r in running_builds:
        if r['name'] == jobName:
            return True
    return False


@run_async
def stopBuildJob(bot, update):
#    bot.sendMessage(update.message.chat_id, text='a')
    running_builds = server.get_running_builds()
    for r in running_builds:
#        bot.sendMessage(update.message.chat_id, text='b')
        if r['name'] == jobName:
            s = 'stop %s#%d, %s' % (r['name'], r['number'], r['url'])
            print s
            server.stop_build(jobName, r['number'])
            bot.sendMessage(update.message.chat_id, text=s)
            return

    s = jobName + strings.NO_JOB_BUILDING
    print s
    bot.sendMessage(update.message.chat_id, text=s)

def error(bot, update, error):
    print 'Update "%s" caused error "%s"' % (update, error)

def listAllowed(bot,update):
    s=""
    for username in config.allowed_users:
       s= '\n'.join([s, '%s ' % (username)])
    bot.sendMessage(update.message.chat_id, text=s)

def help(bot, update):
    s = '\n'.join(
            ['/help # get help', 
                '/build # bot will build a job to get csv',
		'/list # list all user have acces to run /build',
		'/add # add user ex: /add @alexfman',
		'/remove # remove user ex: /remove @alexfman',
                '/stop # stop build '])
    bot.sendMessage(update.message.chat_id, text=s)
def main():
    # init jenkins
    init(config.jenkins_url, config.jenkins_username, config.jenkins_token)
    # Create the EventHandler and pass it your bot's token
    updater = Updater(config.telegram_bot_token)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # add command handlers
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("list", listAllowed))
    dp.add_handler(CommandHandler("build", startBuildJob))
    dp.add_handler(CommandHandler("stop", stopBuildJob)) 
    dp.add_handler(CommandHandler("add", addUser, pass_args=True))
    dp.add_handler(CommandHandler("remove", rmUser, pass_args=True))
    # log all errors
    dp.add_error_handler(error)

    # start bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
