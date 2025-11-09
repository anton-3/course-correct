<div align="center">
    <img width="250" height="250" alt="images" src="frontend/public/courses.png" style="vertical-align: middle;"/>
    <img src="https://d112y698adiu2z.cloudfront.net/photos/production/software_photos/003/955/622/datas/original.png" width="500" style="vertical-align: middle;" />

<br>
<br>

<h1>Course Correct</h1>

Available at <a href="https://correct.courses">correct.courses</a> courtesy of <a href="https://www.godaddy.com/">GoDaddy</a>

</div>

Course Correct is a space themed University scheduling assistant whose purpose is to help students create their class schedule using the most up-to-date class information, knowledge of their previously taken courses, and the requirements listed for their specific major, all powered by a Google Gemini-based AI agent. Users start by uploading a transcript, and the agent does the rest!

In addition to performing basic scheduling tasks, Course Correct maintains a conversation with the user and makes course suggestions based on their preferences, including gathering RateMyProfessor reviews to steer students toward professors more tailored to their learning style.

<div align="center">
  <img src="https://d112y698adiu2z.cloudfront.net/photos/production/software_photos/003/955/628/datas/original.png" width="400" style="vertical-align: middle;" />
  <img src="https://d112y698adiu2z.cloudfront.net/photos/production/software_photos/003/955/624/datas/original.png" width="400" style="vertical-align: middle;" />
</div>
<br>
<br>

# Technologies

<img align="left" width="170" src="https://static.vecteezy.com/system/resources/previews/055/687/055/non_2x/rectangle-gemini-google-icon-symbol-logo-free-png.png" style="margin-right: 20px;" />

## Gemini

We used Gemini Flash 2.5 to power the AI agent's responses. This gave us the ability to have an agent with quite a few messages, allowed function calls, and lots of data in the context, while still being able to produce sensible and accurate responses to the user's queries. 

<br clear="left"/>
<br>
<br>

<img align="left" width="170" src="https://app.aicontentlabs.com/v2/providers/square-icons/ElevenLabs.png" style="margin-right: 20px;" />

## ElevenLabs

ElevenLabs was use for speech-to-text and text-to-speech capabilities, allowing the user to maintain a conversation with the agent. We chose the Matilda voice, which we felt filled the role of an academic advisor quite well.

<br clear="left"/>
<br>
<br>

<img align="left" width="170" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTmD38KsMgEwahtWc_Nfs5ZVktP9dBc36MUZA&s" style="margin-right: 20px;" />

## Flask

Flask was used for our backend api, allowing our AI agent to access tools written in Python for course scheduling, RateMyProfessor reviews, major requirements, and more.

<br clear="left"/>
<br>
<br>

<img align="left" width="170" src="https://images.icon-icons.com/2108/PNG/512/react_icon_130845.png" style="margin-right: 20px;" />

## React

Our frontend was built on React with TypeScript, providing a beautiful interface to interract with the Course Correct agent, generate schedules, and view chat logs in real time.

<br clear="left"/>
<br>
<br>