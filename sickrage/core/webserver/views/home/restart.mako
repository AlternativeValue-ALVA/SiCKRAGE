<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
<%
try:
    themeSpinner = srThemeName
except NameError:
    themeSpinner = sickrage.app.config.theme_name
%>
<h2>${_('Performing Restart')}</h2>
<div class="messages">
    <div id="shut_down_message">
        ${_('Waiting for SiCKRAGE to shut down:')}
        <img src="${srWebRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="shut_down_loading" />
        <img src="${srWebRoot}/images/yes16.png" height="16" width="16" id="shut_down_success" style="display: none;" />
    </div>
    <div id="restart_message" style="display: none;">
        ${_('Waiting for SiCKRAGE to start again:')}
        <img src="${srWebRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="restart_loading" />
        <img src="${srWebRoot}/images/yes16.png" height="16" width="16" id="restart_success" style="display: none;" />
        <img src="${srWebRoot}/images/no16.png" height="16" width="16" id="restart_failure" style="display: none;" />
    </div>
    <div id="refresh_message" style="display: none;">
        ${_('Loading the default page:')}
        <img src="${srWebRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="refresh_loading" />
    </div>
    <div id="restart_fail_message" style="display: none;">
        ${_('Error: The restart has timed out, perhaps something prevented SiCKRAGE from starting again?')}
    </div>
</div>
</%block>